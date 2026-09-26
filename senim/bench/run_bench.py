"""Run SENIM on a labeled claim set (KazTruth format) and compare it with a single-LLM baseline.

    python -m bench.run_bench --csv bench/kaztruth_seed.csv --mode deep

Writes bench/out/features.jsonl (input for train_weights.py) and bench/out/report.md.
Needs OPENROUTER_API_KEY (and ideally TAVILY_API_KEY) in .env. Costs real API credits.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import time
from pathlib import Path

from senim import llm, net, scoring
from senim.config import settings
from senim.extract import extract
from senim.models import Claim, PhantomResult, ReinterrogationResult
from senim.sensors import alibi, fame, phantom, reinterrogate

from .metrics import prf

OUT = Path(__file__).parent / "out"
POSITIVE = {"contradicted", "suspicious"}   # SENIM says "don't trust this"

BASELINE_SYSTEM = ("Is the following claim factually true? Reply with exactly one word: TRUE, FALSE or UNSURE.")


async def baseline(claim_text: str) -> str:
    reply = await llm.chat(settings.model_fast, [
        {"role": "system", "content": BASELINE_SYSTEM},
        {"role": "user", "content": claim_text},
    ], max_tokens=20)
    word = reply.strip().upper()
    return "FALSE" if "FALSE" in word else ("TRUE" if "TRUE" in word else "UNSURE")


async def run_row(row: dict, mode: str, sem: asyncio.Semaphore) -> dict:
    async with sem:
        _, claims, _ = await extract(row["claim"])
        claim = claims[0] if claims else Claim(id="c1", text=row["claim"], lang=row.get("lang", "ru"))
        claim.checkable = True
        jobs = [alibi.run(claim), fame.run(claim)]
        if mode == "deep":
            jobs += [reinterrogate.run(claim), phantom.run_batch([claim], None)]
        results = await asyncio.gather(*jobs, baseline(row["claim"]), return_exceptions=True)
        a, f = results[0], results[1]
        rei = results[2] if mode == "deep" else ReinterrogationResult(status="skipped")
        ph = results[3].get(claim.id) if mode == "deep" and isinstance(results[3], dict) else PhantomResult(status="skipped")
        base = results[-1]
        for name, r in (("alibi", a), ("fame", f), ("rei", rei), ("phantom", ph), ("baseline", base)):
            if isinstance(r, Exception):
                raise RuntimeError(f"{row['id']}: {name} failed: {r}") from r
        feats = scoring.features(claim, a, rei, ph or PhantomResult(status="skipped"), f, [])
        p = scoring.probability(feats)
        return {
            "id": row["id"], "lang": row.get("lang"), "claim": row["claim"], "gold": row["label"],
            "features": feats, "p_wrong": round(p, 4), "senim_label": scoring.label_for(p, feats),
            "baseline": base, "alibi_backend": a.backend,
        }


def report(rows: list[dict], mode: str, elapsed: float, usage: llm.Usage) -> str:
    rows = [r for r in rows if r["gold"] in ("true", "false")]
    gold = [1 if r["gold"] == "false" else 0 for r in rows]
    senim = [1 if r["senim_label"] in POSITIVE else 0 for r in rows]
    base = [1 if r["baseline"] == "FALSE" else 0 for r in rows]
    alibi_only = [1 if (r["features"]["contradicted_t12"] or r["features"]["contradicted_other"]) else 0 for r in rows]
    lines = [
        f"# KazTruth benchmark — {len(rows)} labeled claims, mode={mode}",
        "",
        f"Weights: {scoring.load_weights()[1]} · time {elapsed:.0f}s · {usage.calls} LLM calls · ${usage.cost_usd:.3f}",
        "",
        "Task: flag FALSE claims (positive class = false claim).",
        "",
        "| System | Precision | Recall | F1 | Accuracy |",
        "|---|---|---|---|---|",
    ]
    for name, pred in (("Single LLM (baseline)", base), ("SENIM alibi only", alibi_only), ("SENIM all sensors", senim)):
        m = prf(gold, pred)
        lines.append(f"| {name} | {m['precision']} | {m['recall']} | {m['f1']} | {m['accuracy']} |")
    lines += ["", "## Per claim", "", "| id | gold | SENIM | P(wrong) | baseline |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['gold']} | {r['senim_label']} | {r['p_wrong']} | {r['baseline']} |")
    if len(rows) < 100:
        lines += ["", f"⚠️ Only {len(rows)} claims: numbers are indicative, not statistically solid. Aim for 200."]
    return "\n".join(lines) + "\n"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(Path(__file__).parent / "kaztruth_seed.csv"))
    ap.add_argument("--mode", choices=["quick", "deep"], default="deep")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=3)
    args = ap.parse_args()
    if not settings.has_llm:
        raise SystemExit("OPENROUTER_API_KEY is not set (copy .env.example to .env and add it).")

    with open(args.csv, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if args.limit:
        rows = rows[: args.limit]
    usage = llm.Usage()
    llm.current_usage.set(usage)
    sem = asyncio.Semaphore(args.concurrency)
    started = time.time()
    out_rows = []
    for coro in asyncio.as_completed([run_row(r, args.mode, sem) for r in rows]):
        try:
            res = await coro
            out_rows.append(res)
            print(f"{res['id']}: gold={res['gold']:5} senim={res['senim_label']:13} p={res['p_wrong']:.2f} base={res['baseline']}")
        except Exception as e:
            print(f"skipped: {e}")
    await net.close()
    out_rows.sort(key=lambda r: r["id"])
    OUT.mkdir(exist_ok=True)
    with open(OUT / "features.jsonl", "w", encoding="utf-8") as fh:
        for r in out_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    text = report(out_rows, args.mode, time.time() - started, usage)
    (OUT / "report.md").write_text(text, encoding="utf-8")
    print("\n" + text)


if __name__ == "__main__":
    asyncio.run(main())
