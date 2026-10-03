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


RANK = {"contradicted": 4, "suspicious": 3, "unconfirmed": 2, "confirmed": 1, "not_checkable": 0}


async def run_row(row: dict, mode: str, sem: asyncio.Semaphore, cascade: bool) -> dict:
    """A row may be split into several claims ("moved to Akmola" + "in 2001"): like a human reader,
    judge the row by its worst claim. LLM calls and cost are counted per row (baseline excluded)."""
    async with sem:
        started = time.time()
        usage = llm.Usage()
        token = llm.current_usage.set(usage)
        try:
            _, claims, _ = await extract(row["claim"])
            claims = [c for c in claims if c.checkable] or [Claim(id="c1", text=row["claim"], lang=row.get("lang", "ru"))]
            results = await asyncio.gather(*[_run_claim(c, mode, cascade) for c in claims])
        finally:
            llm.current_usage.reset(token)
        base = await baseline(row["claim"])
        worst = max(results, key=lambda r: (RANK[r["senim_label"]], r["p_wrong"]))
        return {
            "id": row["id"], "lang": row.get("lang"), "claim": row["claim"], "gold": row["label"],
            "split": row.get("split", ""), "popularity": row.get("popularity", ""), "kind": row.get("kind", ""),
            "features": worst["features"], "p_wrong": worst["p_wrong"], "senim_label": worst["senim_label"],
            "baseline": base, "alibi_backend": worst["alibi_backend"], "n_claims": len(claims),
            "settled_by_sources": all(r["settled"] for r in results),
            "llm_calls": usage.calls, "cost_usd": round(usage.cost_usd, 5), "seconds": round(time.time() - started, 1),
        }


async def _run_claim(claim: Claim, mode: str, cascade: bool) -> dict:
    """The same order as the product: Alibi + Fame first, the witness sensors only if the sources did not
    settle the claim (unless --no-cascade)."""
    a, f = await asyncio.gather(alibi.run(claim), fame.run(claim))
    settled = cascade and scoring.decided_by_sources(a)
    rei, ph = ReinterrogationResult(status="skipped"), PhantomResult(status="skipped")
    if mode == "deep" and not settled:
        rei, phs = await asyncio.gather(reinterrogate.run(claim), phantom.run_batch([claim], None))
        ph = phs.get(claim.id) or ph
    if mode == "deep" and settled:
        rei = ReinterrogationResult(status="skipped", note="not_needed")
    feats = scoring.features(claim, a, rei, ph, f, [])
    p = scoring.probability(feats)
    return {"features": feats, "p_wrong": round(p, 4), "senim_label": scoring.label_for(p, feats),
            "alibi_backend": a.backend, "settled": settled}


def _table(rows: list[dict]) -> list[str]:
    gold = [1 if r["gold"] == "false" else 0 for r in rows]
    systems = (
        ("Single LLM (baseline)", [1 if r["baseline"] == "FALSE" else 0 for r in rows]),
        ("SENIM alibi only", [1 if (r["features"]["contradicted_t12"] or r["features"]["contradicted_other"]) else 0
                              for r in rows]),
        ("SENIM all sensors", [1 if r["senim_label"] in POSITIVE else 0 for r in rows]),
    )
    out = ["| System | Precision | Recall | F1 | Accuracy |", "|---|---|---|---|---|"]
    for name, pred in systems:
        m = prf(gold, pred)
        out.append(f"| {name} | {m['precision']} | {m['recall']} | {m['f1']} | {m['accuracy']} |")
    return out


def _f1(rows: list[dict], senim: bool) -> str:
    gold = [1 if r["gold"] == "false" else 0 for r in rows]
    pred = [1 if (r["senim_label"] in POSITIVE if senim else r["baseline"] == "FALSE") else 0 for r in rows]
    return f"{prf(gold, pred)['f1']}"


def report(rows: list[dict], mode: str, elapsed: float, cascade: bool) -> str:
    rows = [r for r in rows if r["gold"] in ("true", "false")]
    n = len(rows) or 1
    calls = sum(r["llm_calls"] for r in rows)
    cost = sum(r["cost_usd"] for r in rows)
    settled = sum(r["settled_by_sources"] for r in rows)
    lines = [
        f"# KazTruth benchmark — {len(rows)} labeled claims, mode={mode}, cascade={'on' if cascade else 'off'}",
        "",
        f"Weights: {scoring.load_weights()[1]} · wall time {elapsed:.0f}s",
        f"SENIM cost: {calls} LLM calls (≈{calls / n:.1f} per claim) · ${cost:.3f} (≈${cost / n:.4f} per claim) · "
        f"median {sorted(r['seconds'] for r in rows)[len(rows) // 2] if rows else 0}s per claim",
        f"Settled by sources alone (witness sensors skipped): {settled}/{len(rows)}",
        "",
        "Task: flag FALSE claims (positive class = false claim).",
        "",
        "## All claims", "", *_table(rows),
    ]
    test = [r for r in rows if r.get("split") == "test"]
    if test:
        lines += ["", f"## Held-out test split ({len(test)} claims, never used for tuning)", "", *_table(test)]
    for key in ("popularity", "lang", "kind"):
        groups = sorted({r.get(key) for r in rows if r.get(key)})
        if groups:
            lines += ["", f"## F1 by {key}", "", "| " + key + " | n | baseline F1 | SENIM F1 |", "|---|---|---|---|"]
            for g in groups:
                sub = [r for r in rows if r.get(key) == g]
                lines.append(f"| {g} | {len(sub)} | {_f1(sub, False)} | {_f1(sub, True)} |")
    lines += ["", "## Per claim", "", "| id | gold | SENIM | P(wrong) | baseline | calls |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['gold']} | {r['senim_label']} | {r['p_wrong']} | {r['baseline']} | {r['llm_calls']} |")
    if len(rows) < 100:
        lines += ["", f"⚠️ Only {len(rows)} claims: numbers are indicative, not statistically solid. Aim for 200."]
    return "\n".join(lines) + "\n"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(Path(__file__).parent / "kaztruth_seed.csv"))
    ap.add_argument("--mode", choices=["quick", "deep"], default="deep")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--split", choices=["dev", "test"], help="only rows of this split")
    ap.add_argument("--no-cascade", action="store_true", help="always run every sensor (to measure the savings)")
    ap.add_argument("--out", default=str(OUT), help="output folder")
    args = ap.parse_args()
    if not settings.has_llm:
        raise SystemExit("OPENROUTER_API_KEY is not set (copy .env.example to .env and add it).")

    with open(args.csv, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if args.split:
        rows = [r for r in rows if r.get("split") == args.split]
    if args.limit:
        rows = rows[: args.limit]
    cascade = not args.no_cascade
    out_dir = Path(args.out)
    sem = asyncio.Semaphore(args.concurrency)
    started = time.time()
    out_rows = []
    for coro in asyncio.as_completed([run_row(r, args.mode, sem, cascade) for r in rows]):
        try:
            res = await coro
            out_rows.append(res)
            print(f"{res['id']}: gold={res['gold']:5} senim={res['senim_label']:13} p={res['p_wrong']:.2f} base={res['baseline']}")
        except Exception as e:
            print(f"skipped: {e}")
    await net.close()
    out_rows.sort(key=lambda r: r["id"])
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "features.jsonl", "w", encoding="utf-8") as fh:
        for r in out_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    text = report(out_rows, args.mode, time.time() - started, cascade)
    (out_dir / "report.md").write_text(text, encoding="utf-8")
    print("\n" + text)


if __name__ == "__main__":
    asyncio.run(main())
