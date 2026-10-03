"""Build KazTruth-WD: labeled claims about Kazakhstan, generated from Wikidata, with a held-out test split.

    python -m bench.build_kaztruth            # → bench/kaztruth_wd.csv (free: only Wikidata is queried)

Every true claim states a Wikidata value (with a link to the item); every false claim is the same template
with the value mutated (another year, another city), the way AI answers usually go wrong. Entities are
sampled across popularity levels (number of Wikipedia language editions), because AI errs most on rare topics.
Each fact appears once (true OR mutated), and `split` keeps 40% of the facts as a test set that nobody tunes on.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import httpx

from senim.config import settings

SPARQL = "https://query.wikidata.org/sparql"
OUT = Path(__file__).parent / "kaztruth_wd.csv"

PEOPLE = """
SELECT ?p ?ru ?kk ?en ?birth ?death ?placeRu ?placeKk ?placeEn ?links ?sex WHERE {
  ?p wdt:P31 wd:Q5; wdt:P27 wd:Q232; wikibase:sitelinks ?links;
     p:P569/psv:P569 [wikibase:timeValue ?birth; wikibase:timePrecision ?bp].
  FILTER(?bp >= 9 && YEAR(?birth) >= 1800)
  OPTIONAL { ?p wdt:P21 ?sex }
  OPTIONAL { ?p p:P570/psv:P570 [wikibase:timeValue ?death; wikibase:timePrecision ?dp]. FILTER(?dp >= 9) }
  OPTIONAL { ?p wdt:P19 ?place. ?place wdt:P17 wd:Q232; wdt:P31/wdt:P279* wd:Q515.
             ?place rdfs:label ?placeRu FILTER(LANG(?placeRu) = "ru")
             OPTIONAL { ?place rdfs:label ?placeKk FILTER(LANG(?placeKk) = "kk") }
             OPTIONAL { ?place rdfs:label ?placeEn FILTER(LANG(?placeEn) = "en") } }
  ?p rdfs:label ?ru FILTER(LANG(?ru) = "ru")
  OPTIONAL { ?p rdfs:label ?kk FILTER(LANG(?kk) = "kk") }
  OPTIONAL { ?p rdfs:label ?en FILTER(LANG(?en) = "en") }
  FILTER(?links >= %(min)d && ?links <= %(max)d)
} LIMIT 4000
"""

ORGS = """
SELECT ?o ?ru ?kk ?en ?inception ?links WHERE {
  ?o wdt:P17 wd:Q232; wikibase:sitelinks ?links;
     p:P571/psv:P571 [wikibase:timeValue ?inception; wikibase:timePrecision ?ip].
  FILTER(?ip >= 9 && YEAR(?inception) >= 1850)
  VALUES ?cls { wd:Q3918 wd:Q875538 wd:Q902104 wd:Q4830453 wd:Q783794 wd:Q891723 wd:Q33506
                wd:Q24354 wd:Q153562 wd:Q476028 wd:Q1137809 wd:Q11032 wd:Q1002697 }
  ?o wdt:P31 ?cls.
  ?o rdfs:label ?ru FILTER(LANG(?ru) = "ru")
  OPTIONAL { ?o rdfs:label ?kk FILTER(LANG(?kk) = "kk") }
  OPTIONAL { ?o rdfs:label ?en FILTER(LANG(?en) = "en") }
  FILTER(?links >= 2)
} LIMIT 3000
"""

# Russian verbs agree with gender: {ed} → "" / "а" ("родился" / "родилась", "умер" / "умерла").
TEMPLATES = {
    "birth": {"ru": "{name} родил{sya} в {v} году.", "kk": "{name} {v} жылы туған.", "en": "{name} was born in {v}."},
    "death": {"ru": "{name} умер{la} в {v} году.", "kk": "{name} {v} жылы қайтыс болған.", "en": "{name} died in {v}."},
    "place": {"ru": "{name} родил{sya} в городе {v}.", "kk": "{name} {v} қаласында туған.",
              "en": "{name} was born in the city of {v}."},
    "founded": {"ru": "Организация «{name}» основана в {v} году.", "kk": "{name} {v} жылы құрылған.",
                "en": "{name} was founded in {v}."},
}
FEMALE = "http://www.wikidata.org/entity/Q6581072"
THIS_YEAR = 2026
POPULARITY_SHARE = {"famous": 0.3, "known": 0.35, "rare": 0.35}
QUOTA = {"birth": 70, "death": 40, "place": 40, "founded": 50}
LANG_SHARE = (("ru", 0.5), ("kk", 0.25), ("en", 0.25))


def query(sparql: str) -> list[dict]:
    r = httpx.get(SPARQL, params={"query": sparql, "format": "json"}, timeout=120,
                  headers={"User-Agent": settings.user_agent, "Accept": "application/sparql-results+json"})
    r.raise_for_status()
    data = json.loads(r.text, strict=False)   # Wikidata labels sometimes contain raw control characters
    return [{k: v["value"] for k, v in b.items()} for b in data["results"]["bindings"]]


def popularity(links: int) -> str:
    return "famous" if links >= 25 else ("known" if links >= 8 else "rare")


def mutate_year(year: int, rng: random.Random, low: int = 1700) -> int | None:
    """A plausible wrong year: never in the future (that would be trivially false)."""
    options = [year + d for d in (-1, 1, -2, 2, -3, 3, -5, 5, -10, 10, -12, 12) if low <= year + d <= THIS_YEAR]
    return rng.choice(options) if options else None


def display_name(label: str) -> str:
    """Wikidata's Russian "Surname, Name Patronymic" → "Name Patronymic Surname"."""
    if ", " in label:
        last, first = label.split(", ", 1)
        return f"{first} {last}"
    return label


def pick_lang(row: dict, rng: random.Random) -> str | None:
    roll, acc = rng.random(), 0.0
    for lang, share in LANG_SHARE:
        acc += share
        if roll <= acc and row.get(lang):
            return lang
    return "ru" if row.get("ru") else None


def build(seed: int = 2026) -> list[dict]:
    rng = random.Random(seed)
    people = {}
    for lo, hi in ((25, 100000), (8, 24), (3, 7)):
        for row in query(PEOPLE % {"min": lo, "max": hi}):
            people.setdefault(row["p"], row)
    people = list(people.values())
    orgs = list({o["o"]: o for o in query(ORGS)}.values())
    city = lambda item, lang: item.get("place" + lang.capitalize())  # noqa: E731
    cities = {lang: sorted({city(p, lang) for p in people if city(p, lang)}) for lang in ("ru", "kk", "en")}
    facts: list[dict] = []
    count = {k: 0 for k in QUOTA}
    by_pop: dict = {(k, p): 0 for k in QUOTA for p in POPULARITY_SHARE}

    def add(kind: str, item: dict, uri: str, value_in, mutate) -> None:
        """value_in(lang) → the true value written in that language (None if unavailable);
        mutate(lang, value) → a wrong value of the same kind."""
        pop = popularity(int(item["links"]))
        if count[kind] >= QUOTA[kind] or by_pop[(kind, pop)] >= round(QUOTA[kind] * POPULARITY_SHARE[pop]) + 1:
            return
        langs = [l for l in ("ru", "kk", "en") if item.get(l) and value_in(l)]
        lang = pick_lang({l: True for l in langs}, rng) if langs else None
        if not lang:
            return
        value = value_in(lang)
        is_true = rng.random() < 0.5
        shown = value if is_true else mutate(lang, value)
        if not shown or (not is_true and shown == value):
            return
        count[kind] += 1
        by_pop[(kind, pop)] += 1
        female = item.get("sex") == FEMALE
        facts.append({
            "kind": kind, "lang": lang, "label": "true" if is_true else "false",
            "claim": TEMPLATES[kind][lang].format(name=display_name(item[lang]) if lang == "ru" else item[lang],
                                                   v=shown, sya="ась" if female else "ся", la="ла" if female else ""),
            "source_url": uri.replace("http://", "https://"),
            "notes": "" if is_true else f"mutated {kind} (Wikidata: {value})",
            "popularity": popularity(int(item["links"])),
        })

    def other_year(_lang, value):
        y = mutate_year(int(value), rng)
        return str(y) if y else None

    def other_city(lang, value):
        pool = [c for c in cities[lang] if c != value]
        return rng.choice(pool) if pool else None

    # Quotas per popularity level keep famous, known and rare entities in every kind of fact.
    rng.shuffle(people)
    rng.shuffle(orgs)
    for p in people:
        add("birth", p, p["p"], lambda _l, p=p: p["birth"][:4], other_year)
        if p.get("death"):
            add("death", p, p["p"], lambda _l, p=p: p["death"][:4], other_year)
        add("place", p, p["p"], lambda l, p=p: city(p, l), other_city)
    for o in orgs:
        add("founded", o, o["o"], lambda _l, o=o: o["inception"][:4], other_year)

    rng.shuffle(facts)
    test = set(rng.sample(range(len(facts)), k=round(len(facts) * 0.4)))
    return [{"id": f"wd{i + 1:03d}", "lang": f["lang"], "claim": f["claim"], "label": f["label"],
             "source_url": f["source_url"], "notes": f["notes"], "kind": f["kind"],
             "popularity": f["popularity"], "split": "test" if i in test else "dev"}
            for i, f in enumerate(facts)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    rows = build(args.seed)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(f"{len(rows)} claims → {args.out}")
    for key in ("label", "lang", "kind", "popularity", "split"):
        print(f"  {key}: {dict(Counter(r[key] for r in rows))}")


if __name__ == "__main__":
    main()
