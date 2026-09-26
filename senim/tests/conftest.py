"""Test fixtures: a scripted fake LLM and a fake internet, so the whole pipeline runs offline."""

from __future__ import annotations

import json

import pytest

from senim import llm, net
from senim.config import settings
from senim.sensors import alibi, citations as cit_sensor, phantom, reinterrogate
from senim.extract import EXTRACT_SYSTEM

SAMPLE = (
    "Абай Кунанбаев родился в 1847 году в Чингизских горах. "
    "Он умер в 1904 году. "
    "Об этом пишет статья Seitkali, 2021, doi:10.5555/senim.fake.2021."
)

EXTRACTION = {
    "language": "ru",
    "claims": [
        {"text": "Абай Кунанбаев родился в 1847 году.", "span": "Абай Кунанбаев родился в 1847 году",
         "type": "date", "checkable": True, "entity": "Abai Kunanbayev", "entity_kind": "person",
         "question": "В каком году родился Абай Кунанбаев?", "question_alt": "Год рождения Абая Кунанбаева?",
         "answer": "1847", "search_queries": ["Абай Кунанбаев год рождения", "Abai Kunanbayev born"],
         "citation_ids": ["r1"]},
        {"text": "Абай Кунанбаев умер в 1904 году.", "span": "Он умер в 1904 году",
         "type": "date", "checkable": True, "entity": "Abai Kunanbayev", "entity_kind": "person",
         "question": "В каком году умер Абай Кунанбаев?", "question_alt": "Год смерти Абая?",
         "answer": "1904", "search_queries": ["Абай год смерти"], "citation_ids": []},
    ],
    "citations": [{"id": "r1", "raw": "Seitkali, 2021, doi:10.5555/senim.fake.2021", "doi": "10.5555/senim.fake.2021",
                   "url": None, "title": None, "authors": ["Seitkali"], "year": 2021, "venue": None}],
}

WIKI_PAGE = {
    "url": "https://ru.wikipedia.org/wiki/Абай_Кунанбаев",
    "title": "Абай Кунанбаев",
    "text": ("Абай Кунанбаев (10 августа 1845 года — 6 июля 1904 года) — казахский поэт, философ, композитор. "
             "Родился в Чингизских горах Семипалатинского уезда."),
    "snippet_only": False,
}
HISTORY_PAGE = {
    "url": "https://e-history.kz/ru/biography/abai",
    "title": "Абай",
    "text": "Великий казахский поэт Абай Кунанбаев родился в 1845 году и скончался в 1904 году в родных местах.",
    "snippet_only": False,
}


async def fake_backend(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    system = messages[0]["content"] if messages[0]["role"] == "system" else ""
    user = messages[-1]["content"]
    if system.startswith(EXTRACT_SYSTEM[:40]):
        return "```json\n" + json.dumps(EXTRACTION, ensure_ascii=False) + "\n```"
    if system == alibi.JUDGE_SYSTEM:
        if "1847" in user:
            return json.dumps({"assessments": [
                {"source": "S1", "stance": "contradicts",
                 "quote": "Абай Кунанбаев (10 августа 1845 года — 6 июля 1904 года)", "source_says": "1845"},
                {"source": "S2", "stance": "contradicts",
                 "quote": "Абай Кунанбаев родился в 1845 году — это точно", "source_says": "1845"},  # invented: must be rejected
            ], "suggested_correction": "Абай Кунанбаев родился в 1845 году."}, ensure_ascii=False)
        return json.dumps({"assessments": [
            {"source": "S1", "stance": "supports", "quote": "6 июля 1904 года) — казахский поэт"},
            {"source": "S2", "stance": "supports", "quote": "скончался в 1904 году в родных местах"},
        ], "suggested_correction": None}, ensure_ascii=False)
    if system == reinterrogate.WITNESS_SYSTEM:
        if "родился" in user or "рождения" in user:
            return "Абай родился в 1845 году." if "gpt" in model or "gemini" in model else "В 1847 году."
        return "Он умер в 1904 году."
    if system == reinterrogate.CLASSIFY_SYSTEM:
        return json.dumps({"relations": ["unsure"] * user.count("\n")})
    if system == phantom.TWIN_SYSTEM:
        return json.dumps({"twins": [
            {"claim_id": "c1", "fake_entity": "Ерлан Жаксыгалиев", "twin_question": "В каком году родился поэт Ерлан Жаксыгалиев?"},
            {"claim_id": "c2", "fake_entity": "Ерлан Жаксыгалиев", "twin_question": "В каком году умер поэт Ерлан Жаксыгалиев?"},
        ]}, ensure_ascii=False)
    if system == phantom.JUDGE_SYSTEM:
        return json.dumps({"fabricated": [True] * user.count("FICTIONAL")})
    if system.startswith("Is the following claim factually true?"):  # bench baseline
        return "TRUE"
    if system == cit_sensor.SUPPORT_SYSTEM:
        return json.dumps({"stance": "absent", "quote": ""})
    if not system:  # phantom target model, asked like a normal user
        return "Ерлан Жаксыгалиев родился в 1932 году в Семее и прославился поэмой «Дала әні»."
    raise AssertionError(f"unexpected LLM call: {system[:60]!r}")


async def fake_get_json(url, params=None, **kw):
    params = params or {}
    if url.startswith("https://doi.org/api/handles/"):
        return (404, None) if "senim.fake" in url else (200, {"responseCode": 1})
    if "wikipedia.org/w/api.php" in url and params.get("list") == "search":
        return 200, {"query": {"searchinfo": {"totalhits": 0}, "search": []}}
    if "wikidata.org" in url and params.get("action") == "wbsearchentities":
        return 200, {"search": [{"id": "Q296244", "label": "Abai Kunanbayev", "description": "Kazakh poet"}]}
    if "wikidata.org" in url and params.get("action") == "wbgetentities":
        return 200, {"entities": {"Q296244": {"sitelinks": {
            "kkwiki": {"title": "Абай Құнанбайұлы"}, "ruwiki": {"title": "Абай Кунанбаев"},
            "enwiki": {"title": "Abai Kunanbayev"}}}}}
    if "pageviews/per-article" in url:
        return 200, {"items": [{"views": 60_000}] * 12}
    if "archive.org/wayback" in url:
        return 200, {"archived_snapshots": {}}
    return 404, None


async def fake_gather_pages(claim):
    return "wikipedia", claim.search_queries[:2], [WIKI_PAGE, HISTORY_PAGE]


@pytest.fixture
def offline(monkeypatch):
    """Fake LLM + fake network for the whole test."""
    llm.set_backend(fake_backend)
    net.cache_clear()
    monkeypatch.setattr(net, "get_json", fake_get_json)
    monkeypatch.setattr(alibi, "gather_pages", fake_gather_pages)
    monkeypatch.setattr(settings, "witnesses", ["openai/gpt-6-luna", "google/gemini-3.5-flash-lite", "deepseek/deepseek-v4-flash"])
    monkeypatch.setenv("SENIM_WEIGHTS", "/nonexistent/weights.json")
    yield
    llm.set_backend(None)
