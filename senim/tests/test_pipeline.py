import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from senim import llm, net, pipeline
from senim.app import app
from senim.config import settings
from senim.models import CheckRequest
from tests.conftest import SAMPLE


def collect(req: CheckRequest) -> list[dict]:
    async def go():
        return [ev async for ev in pipeline.check(req)]
    return asyncio.run(go())


def test_full_deep_check_offline(offline):
    events = collect(CheckRequest(text=SAMPLE, ui_lang="ru", mode="deep", author_model="openai/gpt-6-luna"))
    names = [e["event"] for e in events]
    assert names[0] == "status" and names[1] == "claims" and names[-1] == "done"
    assert "error" not in names

    verdicts = {e["data"]["claim_id"]: e["data"] for e in events if e["event"] == "verdict"}
    assert set(verdicts) == {"c1", "c2"}

    born = verdicts["c1"]
    assert born["label"] == "contradicted"
    assert "1845" in born["source_quote"]
    assert born["suggested_correction"] == "Абай Кунанбаев родился в 1845 году."
    joined = " ".join(born["reasons"])
    assert "Quote-Lock" in joined                  # the invented quote was rejected
    assert "Ерлан Жаксыгалиев" in joined           # phantom twin shown to the user
    assert "👻" in joined                          # fake DOI flagged

    died = verdicts["c2"]
    assert died["label"] == "confirmed"

    cits = next(e["data"] for e in events if e["event"] == "citations")
    assert cits[0]["verdict"] == "fabricated"

    sensors = {(e["data"]["claim_id"], e["data"]["sensor"]) for e in events if e["event"] == "sensor"}
    assert ("c1", "phantom") in sensors and ("c1", "reinterrogation") in sensors and ("c1", "fame") in sensors


def test_verdict_comes_after_all_its_sensors(offline):
    events = collect(CheckRequest(text=SAMPLE, mode="deep"))
    seen = set()
    for e in events:
        if e["event"] == "sensor":
            seen.add((e["data"]["claim_id"], e["data"]["sensor"]))
        if e["event"] == "verdict":
            cid = e["data"]["claim_id"]
            assert {(cid, s) for s in ("alibi", "fame", "reinterrogation", "phantom")} <= seen


def test_quick_mode_skips_expensive_sensors(offline):
    events = collect(CheckRequest(text=SAMPLE, mode="quick", ui_lang="en"))
    sensors = {e["data"]["sensor"] for e in events if e["event"] == "sensor"}
    assert sensors == {"alibi", "fame"}
    born = next(e["data"] for e in events if e["event"] == "verdict" and e["data"]["claim_id"] == "c1")
    assert born["label"] == "contradicted"
    assert any("says otherwise" in r for r in born["reasons"])   # English templates


def test_kazakh_explanations(offline):
    events = collect(CheckRequest(text=SAMPLE, mode="deep", ui_lang="kk"))
    born = next(e["data"] for e in events if e["event"] == "verdict" and e["data"]["claim_id"] == "c1")
    assert any("басқаша айтады" in r for r in born["reasons"])
    assert born["tip"].startswith("Өзіңіз тексеріңіз")


def test_crashing_sensor_does_not_block_verdicts(offline, monkeypatch):
    from senim.sensors import fame

    async def boom(claim):
        raise RuntimeError("wikidata down")
    monkeypatch.setattr(fame, "run", boom)
    events = collect(CheckRequest(text=SAMPLE, mode="quick"))
    assert len([e for e in events if e["event"] == "verdict"]) == 2
    fame_results = [e["data"]["result"] for e in events if e["event"] == "sensor" and e["data"]["sensor"] == "fame"]
    assert all(r["status"] == "error" for r in fame_results)


def test_no_key_gives_clear_error(monkeypatch):
    llm.set_backend(None)
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    events = collect(CheckRequest(text=SAMPLE))
    assert events[0]["event"] == "error" and events[0]["data"]["code"] == "no_llm_key"
    assert events[-1]["event"] == "done"


def test_too_short_input(offline):
    events = collect(CheckRequest(text="коротко"))
    assert events[0]["data"]["code"] == "too_short"


def parse_sse(body: str) -> list[dict]:
    out = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.split("\n") if ": " in line)
        out.append({"event": lines["event"], "data": json.loads(lines["data"])})
    return out


def test_http_api_streams_sse(offline):
    with TestClient(app) as c:
        health = c.get("/api/health").json()
        assert "author_models" in health and "weights" in health
        r = c.post("/api/check", json={"text": SAMPLE, "mode": "quick", "ui_lang": "ru"})
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
        events = parse_sse(r.text)
        assert events[-1]["event"] == "done"
        assert sum(e["event"] == "verdict" for e in events) == 2
        assert c.get("/").status_code == 200


def test_safe_fetch_blocks_internal_addresses():
    async def go(url):
        return await net.safe_fetch(url)
    for url in ["http://127.0.0.1:8000/admin", "http://localhost/", "file:///etc/passwd", "http://10.0.0.5/"]:
        with pytest.raises(net.UnsafeURL):
            asyncio.run(go(url))
