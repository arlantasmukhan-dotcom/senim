"""Sensor 4 — FAME METER: how much could an AI have read about this entity?

LLM accuracy collapses on long-tail (rarely written-about) entities (Mallen et al., ACL 2023 — PopQA
uses Wikipedia pageviews as the popularity measure). We link the entity to Wikidata and sum the
last 12 months of pageviews of its kk/ru/en Wikipedia articles.
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta
from urllib.parse import quote

from .. import net
from ..models import Claim, FameResult

WIKIS = ("kk", "ru", "en")
FAMOUS, KNOWN = 1_000_000, 10_000       # yearly views across kk+ru+en; heuristic thresholds, tune on KazTruth
TAIL_RISK = {"famous": 0.0, "known": 0.35, "rare": 0.7, "unknown": 1.0}


def bucket_for(total_views: int, has_article: bool) -> str:
    if not has_article:
        return "unknown"
    if total_views >= FAMOUS:
        return "famous"
    if total_views >= KNOWN:
        return "known"
    return "rare"


def last_12_months(today: date | None = None) -> tuple[str, str]:
    today = today or date.today()
    end = today.replace(day=1) - timedelta(days=1)                 # last day of previous month
    start = date(end.year - 1, end.month, 1) + timedelta(days=32)  # first day ~12 months back
    start = start.replace(day=1)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


class WikimediaUnavailable(Exception):
    pass


async def find_entity(name: str, lang: str) -> tuple[str, str, str] | None:
    """None = Wikidata answered and has no such entity. Raises if Wikidata could not be reached,
    because "could not check" must never look like "nobody wrote about this" (max tail risk)."""
    answered = False
    for l in dict.fromkeys([lang if lang in WIKIS else "en", "en", "ru"]):
        status, data = await net.get_json("https://www.wikidata.org/w/api.php", {
            "action": "wbsearchentities", "search": name, "language": l, "uselang": l,
            "limit": 1, "format": "json",
        })
        if status != 200 or data is None:
            continue
        answered = True
        hits = data.get("search", [])
        if hits:
            h = hits[0]
            return h["id"], h.get("label", name), h.get("description", "")
    if not answered:
        raise WikimediaUnavailable(f"Wikidata unreachable (last HTTP {status})")
    return None


async def sitelinks(qid: str) -> dict[str, str]:
    status, data = await net.get_json("https://www.wikidata.org/w/api.php", {
        "action": "wbgetentities", "ids": qid, "props": "sitelinks",
        "sitefilter": "|".join(f"{w}wiki" for w in WIKIS), "format": "json",
    })
    if status != 200 or data is None:
        raise WikimediaUnavailable(f"Wikidata sitelinks unavailable (HTTP {status})")
    links = (data.get("entities", {}).get(qid, {}) or {}).get("sitelinks", {})
    return {k[:-4]: v["title"] for k, v in links.items() if k.endswith("wiki") and "title" in v}


async def pageviews(lang: str, title: str) -> int:
    start, end = last_12_months()
    article = quote(title.replace(" ", "_"), safe="")
    url = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
           f"{lang}.wikipedia/all-access/user/{article}/monthly/{start}/{end}")
    status, data = await net.get_json(url)
    if status == 404:          # article has no pageview data: genuinely ~0 views
        return 0
    if status != 200 or data is None:
        raise WikimediaUnavailable(f"pageviews unavailable (HTTP {status})")
    return sum(int(i.get("views", 0)) for i in data.get("items", []))


async def run(claim: Claim) -> FameResult:
    if not claim.entity:
        return FameResult(status="skipped", tail_risk=0.5, note="no named entity in this claim")
    try:
        found = await find_entity(claim.entity, claim.lang)
        if not found:
            return FameResult(status="ok", bucket="unknown", tail_risk=TAIL_RISK["unknown"],
                              note=f"'{claim.entity}' not found on Wikidata")
        qid, label, desc = found
        links = await sitelinks(qid)
        views = dict(zip(links, await asyncio.gather(*[pageviews(l, t) for l, t in links.items()])))
    except Exception as e:
        return FameResult(status="error", tail_risk=0.5, note=f"Wikimedia lookup failed: {e}")
    total = sum(views.values())
    bucket = bucket_for(total, bool(links))
    return FameResult(status="ok", qid=qid, label=label, description=desc, sitelinks=links,
                      views=views, total_views=total, bucket=bucket, tail_risk=TAIL_RISK[bucket])
