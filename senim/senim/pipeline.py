"""Orchestration: extract claims, run all sensors in parallel, stream results as they arrive."""

from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncIterator, Awaitable

from . import explain, llm, scoring
from .config import settings
from .extract import extract
from .models import (AlibiResult, CheckRequest, CitationResult, Claim, FameResult, PhantomResult,
                     ReinterrogationResult)
from .sensors import alibi, citations, fame, phantom, reinterrogate

SENSOR_ERROR = {
    "alibi": lambda msg: AlibiResult(status="error", note=msg),
    "fame": lambda msg: FameResult(status="error", tail_risk=0.5, note=msg),
    "reinterrogation": lambda msg: ReinterrogationResult(status="error", note=msg),
}


def _event(name: str, data: Any) -> dict:
    return {"event": name, "data": data}


def _dump(x):
    if isinstance(x, list):
        return [_dump(i) for i in x]
    return x.model_dump() if hasattr(x, "model_dump") else x


async def check(req: CheckRequest) -> AsyncIterator[dict]:
    usage = llm.Usage()
    token = llm.current_usage.set(usage)
    started = time.time()
    try:
        try:
            async for ev in _check(req):
                yield ev
        except Exception as e:  # last-resort guard: report instead of dropping the stream
            yield _event("error", {"code": "internal", "message": f"{type(e).__name__}: {e}"})
        yield _event("done", {
            "elapsed_s": round(time.time() - started, 1),
            "llm_calls": usage.calls,
            "tokens": usage.prompt_tokens + usage.completion_tokens,
            "cost_usd": round(usage.cost_usd, 4),
            "weights": scoring.load_weights()[1],
        })
    finally:
        try:
            llm.current_usage.reset(token)
        except ValueError:  # generator finalized in another context (client disconnected)
            pass


async def _check(req: CheckRequest) -> AsyncIterator[dict]:
    text = (req.text or "").strip()
    if len(text) < 20:
        yield _event("error", {"code": "too_short", "message": "Text is too short to check."})
        return
    truncated = len(text) > settings.max_input_chars
    text = text[: settings.max_input_chars]
    if not llm.available():
        yield _event("error", {"code": "no_llm_key",
                               "message": "OPENROUTER_API_KEY is not set on the server (see .env.example)."})
        return

    yield _event("status", {"stage": "extract", "truncated": truncated})
    try:
        lang, claims, cits = await extract(text, req.question)
    except llm.LLMError as e:
        yield _event("error", {"code": "extract_failed", "message": str(e)})
        return
    yield _event("claims", {"lang": lang, "text": text, "claims": _dump(claims), "citations": _dump(cits)})
    if not claims:
        return

    deep = req.mode == "deep"
    ui = req.ui_lang
    queue: asyncio.Queue = asyncio.Queue()
    results: dict[str, dict[str, Any]] = {c.id: {} for c in claims}
    cit_results: list[CitationResult] | None = None

    async def guard(kind: str, claim_id: str | None, coro: Awaitable) -> None:
        try:
            res = await coro
        except Exception as e:  # a crashing sensor must never block the verdict
            if kind in SENSOR_ERROR:
                res = SENSOR_ERROR[kind](f"sensor crashed: {e}")
            elif kind == "phantom":
                res = {c.id: PhantomResult(status="error", note=f"sensor crashed: {e}") for c in claims}
            else:
                res = []
        await queue.put((kind, claim_id, res))

    tasks = []
    checkable = [c for c in claims if c.checkable]
    for c in checkable:
        tasks.append(guard("alibi", c.id, alibi.run(c)))
        tasks.append(guard("fame", c.id, fame.run(c)))
        if deep:
            tasks.append(guard("reinterrogation", c.id, reinterrogate.run(c)))
    if deep and checkable:
        tasks.append(guard("phantom", None, phantom.run_batch(checkable, req.author_model)))
    tasks.append(guard("citations", None, citations.run(cits, claims)))
    running = [asyncio.create_task(t) for t in tasks]

    required = {"alibi", "fame"} | ({"reinterrogation", "phantom"} if deep else set())
    done_claims: set[str] = set()

    # Non-checkable claims get their verdict immediately.
    for c in claims:
        if not c.checkable:
            done_claims.add(c.id)
            v = explain.build_verdict(c, "not_checkable", None, {}, AlibiResult(status="skipped"),
                                      ReinterrogationResult(status="skipped"), PhantomResult(status="skipped"),
                                      FameResult(status="skipped"), [], ui)
            yield _event("verdict", _dump(v))

    def ready(c: Claim) -> bool:
        return cit_results is not None and required <= results[c.id].keys()

    try:
        for _ in range(len(running)):
            kind, claim_id, res = await queue.get()
            if kind == "phantom":
                for cid, r in res.items():
                    if cid in results:
                        results[cid]["phantom"] = r
                        yield _event("sensor", {"claim_id": cid, "sensor": "phantom", "result": _dump(r)})
            elif kind == "citations":
                cit_results = res
                for c in cit_results:
                    c.reason = explain.citation_reason(c, ui)
                yield _event("citations", _dump(res))
            else:
                results[claim_id][kind] = res
                yield _event("sensor", {"claim_id": claim_id, "sensor": kind, "result": _dump(res)})

            for c in checkable:
                if c.id in done_claims or not ready(c):
                    continue
                done_claims.add(c.id)
                r = results[c.id]
                rei = r.get("reinterrogation") or ReinterrogationResult(status="skipped", note="quick mode")
                ph = r.get("phantom") or PhantomResult(status="skipped", note="quick mode")
                my_cits = [x for x in cit_results if c.id in x.claim_ids]
                feats = scoring.features(c, r["alibi"], rei, ph, r["fame"], my_cits)
                p = scoring.probability(feats)
                label = scoring.label_for(p, feats)
                v = explain.build_verdict(c, label, p, feats, r["alibi"], rei, ph, r["fame"], my_cits, ui)
                yield _event("verdict", _dump(v))
    finally:
        for t in running:
            if not t.done():
                t.cancel()
