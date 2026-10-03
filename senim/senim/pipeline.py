"""Orchestration: extract claims, run all sensors in parallel, stream results as they arrive."""

from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncIterator, Awaitable

from . import explain, guard, llm, scoring
from .config import AUTHOR_MODELS, settings
from .extract import extract
from .models import (AlibiResult, CheckRequest, CitationResult, Claim, FameResult, PhantomResult,
                     ReinterrogationResult)
from .sensors import alibi, citations, fame, phantom, reinterrogate

AUTHOR_MODEL_IDS = {m["id"] for m in AUTHOR_MODELS}

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
    slots_token = llm.request_slots.set(llm.new_request_slots())
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
            await guard.record_spend(usage.cost_usd)
        except Exception:
            pass
        try:
            llm.current_usage.reset(token)
            llm.request_slots.reset(slots_token)
        except ValueError:  # generator finalized in another context (client disconnected)
            pass


NOT_NEEDED = "not_needed"   # sensor skipped by the cascade: the sources already settled the claim


def _same_claim(a: Claim, b: Claim) -> bool:
    """A claim started while extraction was streaming is reused only if the final build made the same claim."""
    skip = {"citation_ids"}
    return a.model_dump(exclude=skip) == b.model_dump(exclude=skip)


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

    deep = req.mode == "deep"
    ui = req.ui_lang
    author = req.author_model if req.author_model in AUTHOR_MODEL_IDS else None
    queue: asyncio.Queue = asyncio.Queue()
    flows: dict[str, tuple[Claim, asyncio.Task]] = {}      # claim id -> (claim, its sensor flow)
    decisions: dict[str, asyncio.Future] = {}             # claim id -> True if the sources settled it
    loop = asyncio.get_running_loop()

    async def sensor(kind: str, claim: Claim, coro: Awaitable):
        try:
            return await coro
        except Exception as e:  # a crashing sensor must never block the verdict
            return SENSOR_ERROR[kind](f"sensor crashed: {e}")

    async def claim_flow(c: Claim, decided: asyncio.Future) -> None:
        """Alibi and Fame first; the paid witness checks only if the sources did not settle the claim."""
        async def fame_part():
            await queue.put((c.id, "fame", await sensor("fame", c, fame.run(c))))
        fame_task = asyncio.create_task(fame_part())
        try:
            a = await sensor("alibi", c, alibi.run(c))
            await queue.put((c.id, "alibi", a))
            settled = deep and settings.cascade and scoring.decided_by_sources(a)
            if not decided.done():
                decided.set_result(settled)
            if deep and settled:
                await queue.put((c.id, "reinterrogation", ReinterrogationResult(status="skipped", note=NOT_NEEDED)))
                await queue.put((c.id, "phantom", PhantomResult(status="skipped", note=NOT_NEEDED)))
            elif deep:
                await queue.put((c.id, "reinterrogation", await sensor("reinterrogation", c, reinterrogate.run(c))))
            await fame_task
        finally:
            fame_task.cancel()

    def start(c: Claim) -> None:
        if not c.checkable or c.id in flows:
            return
        decisions[c.id] = loop.create_future()
        flows[c.id] = (c, asyncio.create_task(claim_flow(c, decisions[c.id])))

    def stop(cid: str) -> None:
        claim, task = flows.pop(cid)
        task.cancel()
        decisions.pop(cid, None)

    try:
        yield _event("status", {"stage": "extract", "truncated": truncated})
        try:
            lang, claims, cits = await extract(text, req.question, on_claim=start)
        except llm.LLMError as e:
            yield _event("error", {"code": "extract_failed", "message": str(e)})
            return
        # Keep the checks started during streaming only where the final claim is identical.
        final = {c.id: c for c in claims}
        for cid in list(flows):
            if cid not in final or not final[cid].checkable or not _same_claim(flows[cid][0], final[cid]):
                stop(cid)
        kept = []
        while not queue.empty():   # results of stopped flows must not reach the user
            item = queue.get_nowait()
            if item[0] in flows:
                kept.append(item)
        for item in kept:
            queue.put_nowait(item)
        for c in claims:
            start(c)

        yield _event("claims", {"lang": lang, "text": text, "claims": _dump(claims), "citations": _dump(cits)})
        if not claims:
            return

        async def citations_part():
            try:
                res = await citations.run(cits, claims)
            except Exception:
                res = []
            await queue.put((None, "citations", res))

        async def phantom_part():
            settled = await asyncio.gather(*[decisions[c.id] for c in checkable])
            open_claims = [c for c, done in zip(checkable, settled) if not done]
            if not open_claims:
                return
            try:
                res = await phantom.run_batch(open_claims, author)
            except Exception as e:
                res = {c.id: PhantomResult(status="error", note=f"sensor crashed: {e}") for c in open_claims}
            for cid, r in res.items():
                await queue.put((cid, "phantom", r))

        checkable = [c for c in claims if c.checkable]
        workers = [task for _, task in flows.values()] + [asyncio.create_task(citations_part())]
        if deep and checkable:
            workers.append(asyncio.create_task(phantom_part()))

        async def close_queue():
            await asyncio.gather(*workers, return_exceptions=True)
            await queue.put(None)
        closer = asyncio.create_task(close_queue())

        results: dict[str, dict[str, Any]] = {c.id: {} for c in claims}
        cit_results: list[CitationResult] | None = None
        required = {"alibi", "fame"} | ({"reinterrogation", "phantom"} if deep else set())
        has_refs = {c.id: any(c.id in r.claim_ids for r in cits) for c in claims}
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
            # A claim without references never waits for other claims' references to be checked.
            return required <= results[c.id].keys() and (cit_results is not None or not has_refs[c.id])

        while (item := await queue.get()) is not None:
            claim_id, kind, res = item
            if kind == "citations":
                cit_results = res
                for r in cit_results:
                    r.reason = explain.citation_reason(r, ui)
                yield _event("citations", _dump(res))
            elif claim_id in results:
                results[claim_id][kind] = res
                yield _event("sensor", {"claim_id": claim_id, "sensor": kind, "result": _dump(res)})

            for c in checkable:
                if c.id in done_claims or not ready(c):
                    continue
                done_claims.add(c.id)
                r = results[c.id]
                rei = r.get("reinterrogation") or ReinterrogationResult(status="skipped", note="quick mode")
                ph = r.get("phantom") or PhantomResult(status="skipped", note="quick mode")
                my_cits = [x for x in (cit_results or []) if c.id in x.claim_ids]
                feats = scoring.features(c, r["alibi"], rei, ph, r["fame"], my_cits)
                p = scoring.probability(feats)
                label = scoring.label_for(p, feats)
                v = explain.build_verdict(c, label, p, feats, r["alibi"], rei, ph, r["fame"], my_cits, ui)
                yield _event("verdict", _dump(v))
        await closer
    finally:
        for _, task in list(flows.values()):
            if not task.done():
                task.cancel()
