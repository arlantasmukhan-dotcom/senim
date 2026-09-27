"""Step 1: split an AI answer into atomic, checkable claims and find its citations."""

from __future__ import annotations

import re

from . import llm
from .config import settings
from .models import UNCHECKABLE_TYPES, Citation, Claim
from .text import locate_span, numbers

VALID_TYPES = {
    "number", "date", "quote", "citation", "law", "name_fact",
    "causal", "general", "opinion", "advice", "prediction",
}

EXTRACT_SYSTEM = """You are the claim extractor of SENIM, a fact-checking tool for AI answers.
Split the AI ANSWER into atomic factual claims and list its bibliographic citations.

Rules for claims:
- One fact per claim. Make each claim self-contained: replace pronouns with names ("He was born..." -> "Abai Kunanbayev was born...").
- Write "text" in the SAME language as the answer.
- "span": copy, character for character, the shortest piece of the ANSWER that states this claim. Never paraphrase the span.
- "type": one of number, date, quote, citation, law, name_fact, causal, general, opinion, advice, prediction.
  Use "law" for statements about laws/regulations, "quote" for attributed quotations, "citation" when the claim is "source X says Y".
- "checkable": false for opinions, advice, predictions and value judgements.
- "entity": the main real-world entity the claim is about (person/place/organization/event/work), its most common name. null if none.
- "entity_kind": person, place, organization, event, work, concept or other.
- "question": a natural question whose answer is the key fact of the claim (same language as the answer).
- "question_alt": the same question worded differently.
- "answer": the key fact AS STATED IN THE ANSWER, as short as possible (e.g. "1847", "Astana", "45 words").
  Copy the answer's value even if you believe it is wrong. NEVER correct, update or "fix" facts anywhere:
  you are extracting what the AI said, not what is true. Checking happens later.
- "search_queries": 2 web search queries to verify the claim: one in the answer's language and one in Russian (or English if the answer is Russian).
- "citation_ids": ids of citations from the answer that are attached to this claim.
Prioritize specific facts (numbers, dates, names, laws, quotes). At most {max_claims} claims.

Rules for citations (references, papers, books, laws, links mentioned in the answer):
- id "r1", "r2"...; "raw": the reference exactly as written; plus doi, url, title, authors (list of surnames), year, venue when present, else null.

Reply with ONLY this JSON:
{{"language": "kk|ru|en|other",
  "claims": [{{"text": "", "span": "", "type": "", "checkable": true, "entity": "", "entity_kind": "",
              "question": "", "question_alt": "", "answer": "", "search_queries": ["", ""], "citation_ids": []}}],
  "citations": [{{"id": "r1", "raw": "", "doi": null, "url": null, "title": null, "authors": [], "year": null, "venue": null}}]}}"""

DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"'<>«»]+", re.I)
URL_RE = re.compile(r"https?://[^\s<>\"'«»()\[\]]+", re.I)
_TRAIL = ".,;:)]}»\"'”"


def _clean(token: str) -> str:
    return token.rstrip(_TRAIL)


def find_dois(text: str) -> list[str]:
    seen, out = set(), []
    for m in DOI_RE.finditer(text or ""):
        doi = _clean(m.group(0)).lower()
        if doi not in seen:
            seen.add(doi)
            out.append(doi)
    return out


def find_urls(text: str) -> list[str]:
    seen, out = set(), []
    for m in URL_RE.finditer(text or ""):
        url = _clean(m.group(0))
        if "doi.org/" in url.lower():
            continue  # handled as DOI
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def _as_int(v) -> int | None:
    try:
        return int(str(v)[:4]) if v not in (None, "") else None
    except ValueError:
        return None


def _normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", doi.strip(), flags=re.I)
    doi = _clean(doi).lower()
    return doi if doi.startswith("10.") else None


_NUM_IN_ORDER = re.compile(r"\d+(?:[.,]\d+)?")


def faithful_answer(key_fact: str | None, claim_text: str) -> str | None:
    """Guard against the extractor 'correcting' the claim: the key fact's numbers must come from the
    claim itself. If the extractor wrote 1845 for a claim that says 1847, fall back to the claim's numbers."""
    if not key_fact:
        return key_fact
    stated = numbers(claim_text)
    given = numbers(key_fact)
    if given and not given <= stated:
        return " ".join(dict.fromkeys(_NUM_IN_ORDER.findall(claim_text))) or None
    return key_fact


def build(answer: str, data: dict) -> tuple[str, list[Claim], list[Citation]]:
    """Turn the extractor's JSON into validated Claim/Citation objects. Pure function (tested)."""
    lang = (data.get("language") or "ru").lower()
    if lang not in ("kk", "ru", "en"):
        lang = "other"

    citations: list[Citation] = []
    for i, c in enumerate(data.get("citations") or [], 1):
        if not isinstance(c, dict):
            continue
        citations.append(Citation(
            id=str(c.get("id") or f"r{i}"),
            raw=str(c.get("raw") or c.get("title") or c.get("url") or c.get("doi") or "")[:500],
            doi=_normalize_doi(c.get("doi")),
            url=(c.get("url") or None),
            title=c.get("title") or None,
            authors=[str(a) for a in (c.get("authors") or []) if a][:10],
            year=_as_int(c.get("year")),
            venue=c.get("venue") or None,
        ))

    # Safety net: every DOI / URL literally present in the answer becomes a citation even if the LLM missed it.
    known_dois = {c.doi for c in citations if c.doi}
    known_urls = {c.url for c in citations if c.url}
    for doi in find_dois(answer):
        if doi not in known_dois:
            citations.append(Citation(id=f"r{len(citations) + 1}", raw=f"doi:{doi}", doi=doi))
    for url in find_urls(answer):
        if url not in known_urls:
            citations.append(Citation(id=f"r{len(citations) + 1}", raw=url, url=url))

    cit_ids = {c.id for c in citations}
    claims: list[Claim] = []
    for i, c in enumerate(data.get("claims") or [], 1):
        if not isinstance(c, dict) or not (c.get("text") or "").strip():
            continue
        ctype = c.get("type") if c.get("type") in VALID_TYPES else "general"
        checkable = bool(c.get("checkable", True)) and ctype not in UNCHECKABLE_TYPES
        span = c.get("span") or None
        loc = locate_span(span, answer) or locate_span(c.get("text"), answer)
        claim = Claim(
            id=f"c{i}",
            text=c["text"].strip(),
            span=answer[loc[0]:loc[1]] if loc else None,
            start=loc[0] if loc else None,
            end=loc[1] if loc else None,
            type=ctype,
            checkable=checkable,
            lang=lang,
            entity=(c.get("entity") or None),
            entity_kind=(c.get("entity_kind") or None),
            question=c.get("question") or None,
            question_alt=c.get("question_alt") or None,
            answer=faithful_answer(str(c["answer"]) if c.get("answer") not in (None, "") else None,
                                   f"{c['text']} {answer[loc[0]:loc[1]] if loc else ''}"),
            search_queries=[q for q in (c.get("search_queries") or []) if isinstance(q, str) and q.strip()][:3]
            or [c["text"].strip()],
            citation_ids=[x for x in (c.get("citation_ids") or []) if x in cit_ids],
        )
        claims.append(claim)
        if len(claims) >= settings.max_claims:
            break

    for claim in claims:
        for cid in claim.citation_ids:
            for cit in citations:
                if cit.id == cid and claim.id not in cit.claim_ids:
                    cit.claim_ids.append(claim.id)
    return lang, claims, citations


async def extract(answer: str, question: str | None = None) -> tuple[str, list[Claim], list[Citation]]:
    user = (f"QUESTION the user asked the AI:\n{question}\n\n" if question else "") + f"AI ANSWER:\n{answer}"
    data = await llm.chat_json(
        settings.model_main,
        [
            {"role": "system", "content": EXTRACT_SYSTEM.format(max_claims=settings.max_claims)},
            {"role": "user", "content": user},
        ],
        max_tokens=4000,
    )
    if not isinstance(data, dict):
        raise llm.LLMError("extractor returned unexpected JSON")
    return build(answer, data)
