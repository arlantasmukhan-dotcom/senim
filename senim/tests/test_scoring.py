import json

from senim import scoring
from senim.models import (AlibiResult, CitationResult, Claim, Evidence, FameResult, PhantomResult,
                          ReinterrogationResult, WitnessAnswer)

CLAIM = Claim(id="c1", text="x", type="date")


def ev(stance, url="https://ru.wikipedia.org/wiki/X", tier=2):
    return Evidence(url=url, domain="ru.wikipedia.org", tier=tier, stance=stance, quote="q" * 20, locked=True)


def witnesses(*rels):
    return ReinterrogationResult(answers=[WitnessAnswer(model="m", phrasing=1, answer="a", relation=r) for r in rels],
                                 agree_share=rels.count("agree") / len(rels),
                                 contradict_share=rels.count("contradict") / len(rels))


def run(alibi, rei=None, ph=None, fame=None, cits=()):
    rei = rei or ReinterrogationResult(status="skipped")
    ph = ph or PhantomResult(status="skipped")
    fame = fame or FameResult(status="ok", bucket="famous", tail_risk=0.0)
    f = scoring.features(CLAIM, alibi, rei, ph, fame, list(cits))
    p = scoring.probability(f, scoring.DEFAULT_WEIGHTS)
    return f, p, scoring.label_for(p, f)


def test_contradicted_by_trusted_source():
    alibi = AlibiResult(evidence=[ev("contradicts")], contradict_tier12=True, contradict_domains=["wikipedia.org"])
    f, p, label = run(alibi, witnesses("contradict", "contradict", "agree"))
    assert label == "contradicted" and p > 0.9


def test_confirmed_needs_locked_support():
    alibi = AlibiResult(evidence=[ev("supports"), ev("supports", "https://e-history.kz/x")],
                        support_domains=["wikipedia.org", "e-history.kz"])
    f, p, label = run(alibi, witnesses("agree", "agree", "agree"))
    assert f["support"] > 0.6 and label == "confirmed"


def test_support_is_capped_so_many_weak_sites_cannot_dominate():
    weak = [ev("supports", f"https://blog{i}.example/x", tier=4) for i in range(20)]
    f, _, _ = run(AlibiResult(evidence=weak))
    assert f["support"] == 1.0  # 20 × 0.4 capped at 3 → 1.0, not 2.67


def test_no_evidence_rare_topic_bluffing_model_is_suspicious():
    f, p, label = run(AlibiResult(), witnesses("unsure", "unsure"), PhantomResult(status="ok", bluff=1.0),
                      FameResult(status="ok", bucket="unknown", tail_risk=1.0))
    assert label == "suspicious"


def test_off_sensors_use_neutral_values():
    f, _, _ = run(AlibiResult(status="off"), fame=FameResult(status="error"))
    assert f["inconsistency"] == 0.5 and f["tail_risk"] == 0.5 and f["phantom_bluff"] == 0.5


def test_fabricated_citation_makes_claim_suspicious():
    cit = CitationResult(citation_id="r1", raw="x", verdict="fabricated", claim_ids=["c1"])
    f, p, label = run(AlibiResult(), cits=[cit])
    assert f["citation_failure"] == 1.0 and label == "suspicious"


def test_trained_weights_file_is_loaded(tmp_path, monkeypatch):
    path = tmp_path / "w.json"
    path.write_text(json.dumps({"weights": {"bias": -9.0}, "source": "KazTruth test"}))
    monkeypatch.setenv("SENIM_WEIGHTS", str(path))
    w, source = scoring.load_weights()
    assert w["bias"] == -9.0 and w["support"] == scoring.DEFAULT_WEIGHTS["support"] and source == "KazTruth test"
