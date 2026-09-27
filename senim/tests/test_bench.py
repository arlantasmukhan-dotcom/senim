import asyncio
import json
import sys

from bench import metrics, run_bench, train_weights
from senim import scoring


def test_prf():
    m = metrics.prf([1, 1, 0, 0], [1, 0, 1, 0])
    assert m == {"precision": 0.5, "recall": 0.5, "f1": 0.5, "accuracy": 0.5, "n": 4}
    assert metrics.prf([0, 0], [0, 0])["f1"] == 0.0


def test_logreg_learns_the_obvious_direction():
    X = [[1.0, 0.0]] * 10 + [[0.0, 1.0]] * 10      # feature 0 → false claim, feature 1 → true claim
    y = [1] * 10 + [0] * 10
    b, w = metrics.fit_logreg(X, y, epochs=800)
    assert w[0] > 0 > w[1]
    assert metrics.cross_validate(X, y, epochs=300)["accuracy"] == 1.0


def test_run_row_offline(offline):
    row = {"id": "t1", "lang": "ru", "claim": "Абай Кунанбаев родился в 1847 году.", "label": "false"}

    async def go():
        return await run_bench.run_row(row, "deep", asyncio.Semaphore(1))
    res = asyncio.run(go())
    assert res["senim_label"] == "contradicted"
    assert set(scoring.FEATURES) <= set(res["features"])
    text = run_bench.report([res], "deep", 1.0, run_bench.llm.Usage())
    assert "SENIM all sensors" in text and "t1" in text


def test_train_weights_writes_file(tmp_path, monkeypatch):
    feats = tmp_path / "features.jsonl"
    rows = []
    for i in range(12):
        false = i % 2 == 0
        f = {k: 0.0 for k in scoring.FEATURES}
        f["contradicted_t12" if false else "support"] = 1.0
        rows.append({"id": str(i), "gold": "false" if false else "true", "features": f})
    feats.write_text("\n".join(json.dumps(r) for r in rows))
    out = tmp_path / "weights.json"
    monkeypatch.setenv("SENIM_WEIGHTS", str(out))
    monkeypatch.setattr(sys, "argv", ["train", "--features", str(feats)])
    train_weights.main()
    data = json.loads(out.read_text())
    assert data["weights"]["contradicted_t12"] > 0 > data["weights"]["support"]
    assert data["source"].startswith("KazTruth n=12")
    assert scoring.load_weights()[1].startswith("KazTruth n=12")
