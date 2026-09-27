"""Sensor 1 — ALIBI CHECK: search for evidence, let an LLM judge read it, keep only quotes that
literally exist on the page (Quote-Lock)."""

from __future__ import annotations

import asyncio

from .. import llm, net
from ..config import settings
from ..models import AlibiResult, Claim, Evidence
from ..sources import TYPE_DOMAINS, domain_of, registrable_domain, tier_of
from ..text import best_passages, numbers, quote_lock
from .reinterrogate import _CENTURY

TAVILY_URL = "https://api.tavily.com/search"
MAX_SOURCES = 5

JUDGE_SYSTEM = """You are the evidence judge of SENIM. You receive ONE claim and several numbered sources.
For EACH source decide its stance toward the claim:
- "supports": the source states the same fact.
- "contradicts": the source states a DIFFERENT value for the SAME fact (another year, number, name, place...),
  so that the claim and the source cannot both be true. A different but compatible fact (about another part,
  period or aspect, e.g. "the east is salty" vs a claim about the west) is "irrelevant", not "contradicts".
  Mind granularity: a more precise value that falls inside the claim's range SUPPORTS it
  (born "870" supports "9th century"; "10 August 1845" supports "1845"; "about 170" supports "around 170").
- "irrelevant": the source does not address this specific fact.
"quote": copy EXACTLY, character for character, one sentence or clause from that source (12-300 characters) that
shows the stance. It is verified automatically against the page; invented or edited quotes are discarded.
Use "" for irrelevant sources.
For claims about numbers or dates the quote MUST contain the number/date itself (e.g. the year);
a quote without it proves nothing and will be discarded.
"source_says": when contradicting, what the source says instead, briefly, in the claim's language.
"suggested_correction": if a source contradicts the claim, the claim rewritten to agree with that source
(claim's language); otherwise null.
Reply with ONLY this JSON:
{"assessments": [{"source": "S1", "stance": "supports|contradicts|irrelevant", "quote": "", "source_says": ""}],
 "suggested_correction": null}"""


async def tavily_search(query: str, include_domains: list[str] | None = None) -> list[dict]:
    body = {"query": query, "max_results": MAX_SOURCES, "search_depth": "basic", "include_raw_content": "text"}
    if include_domains:
        body["include_domains"] = include_domains
    key = f"tavily {query} {include_domains}"
    if (hit := net.cache_get(key)) is not None:
        return hit
    headers = {"Authorization": f"Bearer {settings.tavily_api_key}"}
    r = await net.client().post(TAVILY_URL, json=body, headers=headers, timeout=40)
    if r.status_code == 400:  # older API versions only accept a boolean here
        body["include_raw_content"] = True
        r = await net.client().post(TAVILY_URL, json=body, headers=headers, timeout=40)
    r.raise_for_status()
    pages = []
    for item in r.json().get("results", []):
        raw = item.get("raw_content") or ""
        pages.append({
            "url": item.get("url", ""),
            "title": item.get("title", ""),
            "text": raw or item.get("content", ""),
            "snippet_only": not raw,
        })
    net.cache_put(key, pages)
    return pages


async def wikipedia_search(query: str, lang: str, limit: int = 1) -> list[dict]:
    api = f"https://{lang}.wikipedia.org/w/api.php"
    status, data = await net.get_json(api, {
        "action": "query", "list": "search", "srsearch": query, "srlimit": limit, "format": "json",
    })
    if status != 200 or not data:
        raise net.HTTPError(status, api)  # an outage is an error, not "no sources exist"
    pages = []
    for hit in data.get("query", {}).get("search", [])[:limit]:
        title = hit["title"]
        status, ext = await net.get_json(api, {
            "action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1,
            "titles": title, "format": "json",
        })
        if status != 200 or not ext:
            continue
        for page in ext.get("query", {}).get("pages", {}).values():
            text = page.get("extract") or ""
            if text:
                pages.append({
                    "url": f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    "title": title, "text": text, "snippet_only": False,
                })
    return pages


async def gather_pages(claim: Claim) -> tuple[str, list[str], list[dict]]:
    queries = claim.search_queries[:2] or [claim.text]
    if settings.has_search:
        jobs = [tavily_search(q) for q in queries]
        extra = TYPE_DOMAINS.get(claim.type)
        if extra:
            jobs.append(tavily_search(queries[0], include_domains=extra))
        backend = "tavily"
    else:
        langs = [claim.lang] if claim.lang in ("kk", "ru", "en") else []
        langs += [l for l in ("ru", "en") if l not in langs]
        jobs = []
        for i, lang in enumerate(langs[:3]):
            q = queries[0] if lang == claim.lang else (queries[1] if len(queries) > 1 else (claim.entity or claim.text))
            jobs.append(wikipedia_search(q, lang))
        backend = "wikipedia"
    results = await asyncio.gather(*jobs, return_exceptions=True)
    errors = [r for r in results if isinstance(r, Exception)]
    if errors and len(errors) == len(results):
        raise errors[0]
    pages, seen = [], set()
    for res in results:
        if isinstance(res, Exception):
            continue
        for p in res:
            if p["url"] and p["url"] not in seen and p["text"].strip():
                seen.add(p["url"])
                pages.append(p)
    # Prefer trusted sources when there are too many.
    pages.sort(key=lambda p: tier_of(p["url"]))
    return backend, queries, pages[:MAX_SOURCES]


def _shows_number(stance: str, wanted: set[str], got: set[str]) -> bool:
    """For numeric claims a quote only counts if it shows the number: support must contain the
    claimed value; a contradiction must contain some number and not simply repeat the claim."""
    if stance == "supports":
        return bool(wanted & got)
    return bool(got) and not wanted <= got


def apply_judgement(claim: Claim, pages: list[dict], judgement: dict) -> AlibiResult:
    """Quote-Lock the judge's assessments and compute the alibi features. Pure function (tested)."""
    res = AlibiResult()
    by_id = {f"S{i + 1}": p for i, p in enumerate(pages)}
    wanted = set() if _CENTURY.search(claim.answer or "") else numbers(claim.answer or "")
    best_tier: dict[str, int] = {}
    for a in judgement.get("assessments") or []:
        page = by_id.get(str(a.get("source", "")).strip())
        stance = a.get("stance")
        if not page or stance not in ("supports", "contradicts"):
            continue
        quote = (a.get("quote") or "").strip()
        locked = quote_lock(quote, page["text"])
        ev = Evidence(
            url=page["url"], domain=domain_of(page["url"]), title=page.get("title", ""),
            tier=tier_of(page["url"]), stance=stance, quote=quote, locked=locked,
            snippet_only=page.get("snippet_only", False),
        )
        res.evidence.append(ev)
        if not locked:
            res.rejected_quotes += 1
            continue
        if wanted and not _shows_number(stance, wanted, numbers(quote)):
            ev.stance = "irrelevant"   # real quote, but it doesn't contain the number/date at stake
            res.weak_quotes += 1
            continue
        reg = registrable_domain(page["url"])
        best_tier[reg] = min(best_tier.get(reg, 9), ev.tier)
        if stance == "supports" and reg not in res.support_domains:
            res.support_domains.append(reg)
        if stance == "contradicts":
            if reg not in res.contradict_domains:
                res.contradict_domains.append(reg)
            if ev.tier <= 2:
                res.contradict_tier12 = True
            else:
                res.contradict_other = True
    res.support_domains.sort(key=lambda d: best_tier.get(d, 9))
    res.contradict_domains.sort(key=lambda d: best_tier.get(d, 9))
    if res.contradict_domains and judgement.get("suggested_correction"):
        res.suggested_correction = str(judgement["suggested_correction"])[:400]
    return res


async def run(claim: Claim) -> AlibiResult:
    if not claim.checkable:
        return AlibiResult(status="skipped", note="not a checkable fact")
    if not llm.available():
        return AlibiResult(status="off", note="OPENROUTER_API_KEY not set")
    try:
        backend, queries, pages = await gather_pages(claim)
    except Exception as e:  # search outage must not kill the whole check
        return AlibiResult(status="error", note=f"search failed: {e}")
    if not pages:
        return AlibiResult(status="ok", backend=backend, queries=queries, note="no sources found")

    focus = " ".join(filter(None, [claim.text, claim.answer or "", claim.entity or ""]))
    blocks = [
        f"[S{i + 1}] {p['title']} — {p['url']}\n{best_passages(p['text'], focus)}"
        for i, p in enumerate(pages)
    ]
    user = f"CLAIM: {claim.text}\n\nSOURCES:\n\n" + "\n\n".join(blocks)
    try:
        judgement = await llm.chat_json(settings.model_main, [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user},
        ], max_tokens=2000)
    except llm.LLMError as e:
        return AlibiResult(status="error", backend=backend, queries=queries, note=str(e))
    res = apply_judgement(claim, pages, judgement if isinstance(judgement, dict) else {})
    res.backend, res.queries = backend, queries
    return res
