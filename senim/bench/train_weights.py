"""Fit the Trust Score weights on labeled benchmark results and save them to weights.json.

    python -m bench.run_bench          # first: produces bench/out/features.jsonl
    python -m bench.train_weights      # then: fits weights, compares with default priors (5-fold CV)

The server loads weights.json automatically on the next check.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from senim import scoring

from .metrics import cross_validate, fit_logreg, predict, prf

FEATURES_FILE = Path(__file__).parent / "out" / "features.jsonl"


def load(path: Path) -> tuple[list[list[float]], list[int]]:
    X, y = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("gold") not in ("true", "false"):
            continue
        X.append([float(r["features"].get(k, 0.0)) for k in scoring.FEATURES])
        y.append(1 if r["gold"] == "false" else 0)
    return X, y


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default=str(FEATURES_FILE))
    ap.add_argument("--l2", type=float, default=0.05)
    ap.add_argument("--dry-run", action="store_true", help="report only, don't write weights.json")
    args = ap.parse_args()

    X, y = load(Path(args.features))
    if len(X) < 10 or len(set(y)) < 2:
        raise SystemExit(f"Need at least 10 labeled claims with both labels; got {len(X)}.")

    d = scoring.DEFAULT_WEIGHTS
    default_pred = [1 if predict(d["bias"], [d[k] for k in scoring.FEATURES], x) >= 0.5 else 0 for x in X]
    print("default priors (in-sample):", prf(y, default_pred))
    cv = cross_validate(X, y, l2=args.l2)
    print("trained, 5-fold cross-validation:", cv)

    b, w = fit_logreg(X, y, l2=args.l2)
    weights = {"bias": round(b, 4), **{k: round(v, 4) for k, v in zip(scoring.FEATURES, w)}}
    print("fitted weights:", json.dumps(weights, indent=2))
    if len(X) < 100:
        print(f"⚠️ Only {len(X)} examples — weights will be noisy. Label more claims (target: 200).")
    if args.dry_run:
        return
    out = scoring.weights_path()
    out.write_text(json.dumps({
        "weights": weights,
        "source": f"KazTruth n={len(X)} ({date.today().isoformat()})",
        "cross_validation": cv,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved → {out}")


if __name__ == "__main__":
    main()
