"""Fixes from the second code review: numbers by value, citation matching, cascade, streaming, speed."""

import asyncio
import json

from senim import llm, net, pipeline
from senim.extract import ClaimScanner, faithful_answer
from senim.models import CheckRequest, Citation, Claim
from senim.sensors import alibi, citations, reinterrogate
from senim.sensors.citations import compare_metadata
from senim.sensors.reinterrogate import numeric_relation
from tests.conftest import EXTRACTION, SAMPLE, fake_backend


def collect(req):
    async def go():
        return [ev async for ev in pipeline.check(req)]
    return asyncio.run(go())


# ---- numbers are compared by value, not as strings

def test_witness_numbers_by_value():
    assert numeric_relation("2,7 млн", "Около 2 700 000 человек.") == "agree"
    assert numeric_relation("2,7 млн", "2,700,000 people") == "agree"            # was "contradict"
    assert numeric_relation("20,000", "20 000") == "agree"
    assert numeric_relation("2,7 млн", "3,1 млн человек") == "contradict"
    assert numeric_relation("2,7 млн", "Данные за 2023 год") is None             # a year is not a population
    assert numeric_relation("1845", "Он прожил 59 лет.") is None                 # an age is not a year
    assert numeric_relation("10 августа 1845", "10.08.1845") == "agree"          # dotted date is not 10.08


def test_source_quote_with_other_number_format_supports():
    claim = Claim(id="c", text="В Алматы живёт 2,7 млн человек.", type="number", answer="2,7 млн")
    pages = [{"url": "https://stat.gov.kz/a", "title": "t", "text": "Население Алматы составило 2 700 000 человек."}]
    res = alibi.apply_judgement(claim, pages, {"assessments": [
        {"source": "S1", "stance": "supports", "quote": "Население Алматы составило 2 700 000 человек"}]})
    assert res.support_domains == ["stat.gov.kz"] and res.weak_quotes == 0


def test_faithful_answer_by_value_keeps_scale_words():
    assert faithful_answer("2.7 million", "Население 2,7 млн человек") == "2.7 million"
    assert faithful_answer("3 млн", "Население 2,7 млн человек") == "2,7 млн"


# ---- citations

def test_transliterated_authors_and_subtitles_match():
    cit = Citation(id="r1", raw="x", title="Абай и казахская литература", authors=["Сейткали А."], year=2021)
    assert compare_metadata(cit, "Абай и казахская литература", 2021, ["Seitkali, A."]) == []
    assert compare_metadata(cit, "Абай и казахская литература", 2021, ["Seytkali"]) == []
    cit = Citation(id="r2", raw="x", title="Detecting hallucinations in large language models", authors=["Farquhar"])
    full = "Detecting hallucinations in large language models: a semantic entropy approach"
    assert compare_metadata(cit, full, None, ["Sebastian Farquhar"]) == []
    assert compare_metadata(cit, full, None, ["Ivanov"]) == ["authors"]


def test_doi_lookups_run_in_parallel(monkeypatch):
    running, peak = 0, 0

    async def slow(url, params=None, **kw):
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.05)
        running -= 1
        return (200, {"responseCode": 1}) if "doi.org/api" in url else (404, None)
    monkeypatch.setattr(net, "get_json", slow)
    asyncio.run(citations.check_one(Citation(id="r1", raw="x", doi="10.1/x"), {}))
    assert peak == 3   # doi.org, Crossref and OpenAlex at the same time


# ---- streaming extraction

def test_scanner_yields_each_claim_as_soon_as_it_is_complete():
    reply = "```json\n" + json.dumps(EXTRACTION, ensure_ascii=False) + "\n```"
    reply = reply.replace('"Абай Кунанбаев родился в 1847 году."', '"Абай {родился} в \\"1847\\" году."')
    scanner, got = ClaimScanner(), []
    for i in range(0, len(reply), 7):
        got += scanner.feed(reply[i:i + 7])
        if len(got) == 1:
            assert '"citations"' not in scanner.buf     # first claim came before the reply finished
    assert [i for i, _ in got] == [1, 2] and scanner.lang == "ru"
    assert got[0][1]["text"] == 'Абай {родился} в "1847" году.'


def test_claims_started_while_streaming_are_not_checked_twice(offline, monkeypatch):
    calls = []
    real = alibi.run

    async def counting(claim):
        calls.append(claim.id)
        return await real(claim)
    monkeypatch.setattr(alibi, "run", counting)
    collect(CheckRequest(text=SAMPLE, mode="quick"))
    assert sorted(calls) == ["c1", "c2"]


# ---- cascade and early verdicts

def test_cascade_skips_witnesses_when_sources_settle_the_claim(offline):
    asked = []

    async def spy(model, messages, temperature, max_tokens):
        if messages[0]["content"] == reinterrogate.WITNESS_SYSTEM:
            asked.append(messages[-1]["content"])
        return await fake_backend(model, messages, temperature, max_tokens)
    llm.set_backend(spy)
    events = collect(CheckRequest(text=SAMPLE, mode="deep"))
    sensors = {(e["data"]["claim_id"], e["data"]["sensor"]): e["data"]["result"] for e in events if e["event"] == "sensor"}
    # c2 ("died in 1904") is supported by two trusted sources: no witnesses, no phantom twin.
    assert sensors[("c2", "reinterrogation")]["note"] == pipeline.NOT_NEEDED
    assert sensors[("c2", "phantom")]["note"] == pipeline.NOT_NEEDED
    assert not any("умер" in q for q in asked)
    # c1 has only one quote-locked contradiction: the witnesses are still asked.
    assert sensors[("c1", "reinterrogation")]["status"] == "ok"
    verdicts = {e["data"]["claim_id"]: e["data"] for e in events if e["event"] == "verdict"}
    assert verdicts["c2"]["label"] == "confirmed" and verdicts["c1"]["label"] == "contradicted"
    assert any("не опрашивали" in r for r in verdicts["c2"]["reasons"])


def test_claim_without_references_does_not_wait_for_citation_checks(offline, monkeypatch):
    real = citations.run

    async def slow(cits, claims):
        await asyncio.sleep(0.3)
        return await real(cits, claims)
    monkeypatch.setattr(citations, "run", slow)
    names = [(e["event"], e["data"].get("claim_id") if isinstance(e["data"], dict) else None)
             for e in collect(CheckRequest(text=SAMPLE, mode="quick"))]
    assert names.index(("verdict", "c2")) < names.index(("citations", None)) < names.index(("verdict", "c1"))


# ---- no duplicate work

def test_identical_requests_share_one_network_call(monkeypatch):
    hits = []

    class FakeResponse:
        status_code = 200
        headers = {}

        def json(self):
            return {"ok": True}

    class FakeClient:
        async def get(self, url, params=None):
            hits.append(url)
            await asyncio.sleep(0.05)
            return FakeResponse()
    net.cache_clear()
    monkeypatch.setattr(net, "client", lambda: FakeClient())

    async def run():
        return await asyncio.gather(*[net.get_json("https://www.wikidata.org/x", {"q": "Abai"}) for _ in range(5)])
    assert asyncio.run(run()) == [(200, {"ok": True})] * 5 and len(hits) == 1
