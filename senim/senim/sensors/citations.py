"""Sensor 5 — CITATION AUTOPSY: does each reference exist, do its details match the real record,
and does it actually say what the answer attributes to it?"""

from __future__ import annotations

import asyncio
import re
from urllib.parse import quote

from .. import llm, net
from ..config import settings
from ..models import Citation, CitationResult, Claim
from ..text import normalize, quote_lock, title_similarity

TITLE_MATCH = 0.85
FAILURE_WEIGHT = {"fabricated": 1.0, "frankenstein": 1.0, "never_existed": 1.0, "not_supporting": 0.6, "dead_link": 0.3}
_CYRILLIC = re.compile(r"[а-яёәғқңөұүһі]", re.I)

SUPPORT_SYSTEM = """You receive CLAIMS that an AI attributed to a source, and the SOURCE TEXT (abstract or page).
Decide: "supports" if the source text states the claim(s); "contradicts" if it states something incompatible;
"absent" if the text does not address them. "quote": copy EXACTLY one sentence/clause (12-300 chars) from the
SOURCE TEXT that shows it (it is verified automatically), or "" when absent.
Reply with ONLY JSON: {"stance": "supports|contradicts|absent", "quote": ""}"""


def failure_value(verdict: str) -> float:
    return FAILURE_WEIGHT.get(verdict, 0.0)


def inverted_index_to_text(inv: dict | None) -> str:
    if not inv:
        return ""
    slots: dict[int, str] = {}
    for word, positions in inv.items():
        for p in positions:
            slots[p] = word
    return " ".join(slots[i] for i in sorted(slots))


def name_tokens(names: list[str]) -> set[str]:
    """All name words of 3+ letters ("Farquhar, S." / "Sebastian Farquhar" → {"farquhar", "sebastian"}).
    Initials are dropped. Comparing every word avoids guessing which one is the surname."""
    out = set()
    for n in names:
        for tok in normalize(n).replace(",", " ").replace(".", " ").split():
            if len(tok) >= 3:
                out.add(tok)
    return out


def compare_metadata(cit: Citation, title: str | None, year: int | None, authors: list[str]) -> list[str]:
    """Return what does not match between the cited reference and the real record. Pure (tested)."""
    mismatches = []
    if cit.title and title and title_similarity(cit.title, title) < TITLE_MATCH:
        mismatches.append("title")
    if cit.year and year and abs(cit.year - year) > 1:
        mismatches.append("year")
    if cit.authors and authors:
        claimed, real = name_tokens(cit.authors), name_tokens(authors)
        if claimed and real and not claimed & real:
            mismatches.append("authors")
    return mismatches


async def doi_registered(doi: str) -> bool | None:
    status, _ = await net.get_json(f"https://doi.org/api/handles/{quote(doi, safe='/')}")
    if status == 200:
        return True
    if status == 404:
        return False
    return None


def _crossref_params() -> dict:
    return {"mailto": settings.contact_email} if settings.contact_email else {}


def _from_crossref(item: dict) -> dict:
    parts = (item.get("issued") or item.get("published") or {}).get("date-parts") or [[None]]
    return {
        "title": (item.get("title") or [None])[0],
        "year": parts[0][0] if parts and parts[0] else None,
        "authors": [a.get("family") or a.get("name") or "" for a in item.get("author", [])],
        "abstract": net.html_to_text(item.get("abstract") or ""),
        "doi": item.get("DOI"),
    }


def _from_openalex(item: dict) -> dict:
    return {
        "title": item.get("title") or item.get("display_name"),
        "year": item.get("publication_year"),
        "authors": [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])],
        "abstract": inverted_index_to_text(item.get("abstract_inverted_index")),
        "doi": (item.get("doi") or "").replace("https://doi.org/", "") or None,
    }


async def metadata_by_doi(doi: str) -> tuple[str, dict] | None:
    status, data = await net.get_json(f"https://api.crossref.org/works/{quote(doi, safe='/')}", _crossref_params())
    if status == 200 and data and data.get("message"):
        return "crossref", _from_crossref(data["message"])
    status, data = await net.get_json(f"https://api.openalex.org/works/https://doi.org/{quote(doi, safe='/')}")
    if status == 200 and data:
        return "openalex", _from_openalex(data)
    return None


async def search_by_title(cit: Citation) -> tuple[str, dict] | None:
    query = " ".join(filter(None, [cit.title, " ".join(cit.authors[:2]), str(cit.year or "")]))
    status, data = await net.get_json("https://api.crossref.org/works",
                                      {"query.bibliographic": query, "rows": 3, **_crossref_params()})
    for item in ((data or {}).get("message", {}).get("items", []) if status == 200 else []):
        meta = _from_crossref(item)
        if title_similarity(cit.title, meta["title"]) >= TITLE_MATCH:
            return "crossref", meta
    status, data = await net.get_json("https://api.openalex.org/works", {"search": cit.title, "per-page": 3})
    for item in ((data or {}).get("results", []) if status == 200 else []):
        meta = _from_openalex(item)
        if title_similarity(cit.title, meta["title"]) >= TITLE_MATCH:
            return "openalex", meta
    return None


async def wayback_has(url: str) -> bool:
    status, data = await net.get_json("https://archive.org/wayback/available", {"url": url})
    snap = ((data or {}).get("archived_snapshots") or {}).get("closest") or {}
    return status == 200 and bool(snap.get("available"))


async def check_support(res: CitationResult, claims: list[Claim], source_text: str, abstract_only: bool) -> None:
    if not claims:
        res.verdict = "unchecked"
        res.note = (res.note + " Source exists; no specific claim is attached to it.").strip()
        return
    if not source_text.strip() or not llm.available():
        res.verdict = "unverifiable_text"
        res.note = (res.note + " Source exists, but its text is not available to check the claim.").strip()
        return
    listing = "\n".join(f"- {c.text}" for c in claims)
    try:
        data = await llm.chat_json(settings.model_fast, [
            {"role": "system", "content": SUPPORT_SYSTEM},
            {"role": "user", "content": f"CLAIMS:\n{listing}\n\nSOURCE TEXT:\n{source_text[:6000]}"},
        ], max_tokens=500)
    except llm.LLMError:
        res.verdict = "unverifiable_text"
        return
    stance = (data or {}).get("stance") if isinstance(data, dict) else None
    q = (data or {}).get("quote", "") if isinstance(data, dict) else ""
    locked = quote_lock(q, source_text)
    if stance == "supports" and locked:
        res.verdict, res.support_quote = "supports", q
    elif stance == "contradicts" and locked:
        res.verdict, res.support_quote = "not_supporting", q
    elif abstract_only:
        res.verdict = "unverifiable_text"
        res.note = (res.note + " Only the abstract is available and it does not settle the claim.").strip()
    else:
        res.verdict = "not_supporting"
        res.note = (res.note + " The source text does not state this claim.").strip()


async def check_one(cit: Citation, claims_by_id: dict[str, Claim]) -> CitationResult:
    res = CitationResult(citation_id=cit.id, raw=cit.raw, claim_ids=list(cit.claim_ids))
    linked = [claims_by_id[c] for c in cit.claim_ids if c in claims_by_id]
    try:
        found = None
        if cit.doi:
            registered = await doi_registered(cit.doi)
            if registered is False:
                res.exists, res.verdict, res.lookup = False, "fabricated", "doi.org"
                res.note = "This DOI is not registered with the DOI system."
                return res
            found = await metadata_by_doi(cit.doi)
            res.exists = True if registered else None
            if not found:
                res.lookup = "doi.org"
                if registered:
                    res.verdict = "unverifiable_text"
                    res.note = "The DOI is registered, but no metadata/abstract is available to compare."
                else:
                    res.verdict = "unchecked"
                    res.note = "Could not reach the DOI system to check this reference."
                return res
        elif cit.title:
            found = await search_by_title(cit)
            if not found:
                res.exists = False
                if _CYRILLIC.search(cit.title):
                    res.verdict = "unchecked"
                    res.note = ("Not found in Crossref/OpenAlex. Many Kazakh/Russian journals and books are not "
                                "indexed there, so check it manually (e.g. elibrary, the journal's site).")
                else:
                    res.verdict = "fabricated"
                    res.note = "No publication with this title was found in Crossref or OpenAlex."
                res.lookup = "crossref+openalex"
                return res
        if found:
            res.lookup, meta = found
            res.exists = True
            res.found_title, res.found_year, res.found_authors = meta["title"], meta["year"], meta["authors"][:8]
            res.mismatches = compare_metadata(cit, meta["title"], meta["year"], meta["authors"])
            if res.mismatches:
                res.verdict = "frankenstein"
                res.note = "The source is real, but these details are wrong: " + ", ".join(res.mismatches) + "."
                return res
            await check_support(res, linked, meta.get("abstract") or "", abstract_only=True)
            return res
        if cit.url:
            try:
                status, final_url, body = await net.safe_fetch(cit.url)
            except net.UnsafeURL:
                res.verdict, res.note = "unchecked", "Link points to a private/non-web address; not fetched."
                return res
            res.lookup = "http"
            if status == 0 or status in (404, 410):
                archived = await wayback_has(cit.url)
                res.lookup = "http+wayback"
                res.exists = archived
                res.verdict = "dead_link" if archived else "never_existed"
                res.note = ("The page is gone now, but the Internet Archive has a copy." if archived else
                            "The page does not exist and the Internet Archive has never seen it.")
                return res
            if status >= 400:
                res.verdict, res.note = "unverifiable_text", f"The site answered HTTP {status}; could not read it."
                return res
            res.exists = True
            await check_support(res, linked, net.html_to_text(body), abstract_only=False)
            return res
        res.verdict, res.note = "unchecked", "Reference has no DOI, title or link to check."
        return res
    except Exception as e:
        res.verdict, res.note = "unchecked", f"lookup failed: {e}"
        return res


async def run(citations: list[Citation], claims: list[Claim]) -> list[CitationResult]:
    by_id = {c.id: c for c in claims}
    return list(await asyncio.gather(*[check_one(c, by_id) for c in citations]))
