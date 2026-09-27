"""Combine the five sensors into P(wrong) with a transparent logistic regression, then pick a label.

P(wrong) = sigmoid(b + Σ w_i · x_i). The default weights are hand-set priors; run
`python -m bench.train_weights` on labeled KazTruth data to replace them with fitted ones
(saved to weights.json and loaded automatically).
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

from .config import PROJECT_ROOT
from .models import (AlibiResult, CitationResult, Claim, FameResult, PhantomResult,
                     ReinterrogationResult)
from .sensors.citations import failure_value

FEATURES = [
    "contradicted_t12",    # a tier-1/2 source contradicts the claim (quote-locked)
    "contradicted_other",  # only tier-3/4 sources contradict it
    "support",             # independent quote-locked support, tier-weighted, capped at 3 sources → 0..1
    "inconsistency",       # 1 − share of witness answers that agree
    "witness_contradict",  # share of witness answers that state a different value
    "phantom_bluff",       # share of phantom-twin answers where the model invented facts
    "tail_risk",           # Fame Meter: 0 famous … 1 unknown entity
    "type_risk",           # precise claim types (numbers, dates, quotes, laws, citations) fail more
    "citation_failure",    # worst Citation Autopsy result among the claim's references
]

DEFAULT_WEIGHTS = {
    "bias": -1.2,
    "contradicted_t12": 4.0,
    "contradicted_other": 1.5,
    "support": -3.5,
    "inconsistency": 1.2,
    "witness_contradict": 1.5,
    "phantom_bluff": 0.6,
    "tail_risk": 0.7,
    "type_risk": 0.6,
    "citation_failure": 2.5,
}

# Value used when a sensor could not run (no key, outage, not applicable): "no information either way".
NEUTRAL = {"inconsistency": 0.5, "witness_contradict": 0.0, "phantom_bluff": 0.5, "tail_risk": 0.5}

TYPE_RISK = {
    "number": 1.0, "date": 1.0, "quote": 1.0, "citation": 1.0, "law": 1.0,
    "name_fact": 0.7, "causal": 0.5, "general": 0.3,
}
TIER_WEIGHT = {1: 1.0, 2: 1.0, 3: 0.7, 4: 0.4}

CONFIRMED_MAX = 0.35
CONTRADICTED_MIN = 0.5
SUSPICIOUS_MIN = 0.7


def weights_path() -> Path:
    return Path(os.environ.get("SENIM_WEIGHTS", PROJECT_ROOT / "weights.json"))


def load_weights() -> tuple[dict[str, float], str]:
    p = weights_path()
    if p.exists():
        try:
            data = json.loads(p.read_text())
            w = {k: float(data["weights"].get(k, DEFAULT_WEIGHTS[k])) for k in DEFAULT_WEIGHTS}
            return w, data.get("source", str(p.name))
        except (ValueError, KeyError, TypeError):
            pass
    return dict(DEFAULT_WEIGHTS), "default priors (not yet trained)"


def support_score(alibi: AlibiResult) -> float:
    best: dict[str, float] = {}
    from .sources import registrable_domain
    for ev in alibi.evidence:
        if ev.locked and ev.stance == "supports":
            d = registrable_domain(ev.url)
            best[d] = max(best.get(d, 0.0), TIER_WEIGHT.get(ev.tier, 0.4))
    return min(sum(best.values()), 3.0) / 3.0


def features(claim: Claim, alibi: AlibiResult, rei: ReinterrogationResult, ph: PhantomResult,
             fame: FameResult, cits: list[CitationResult]) -> dict[str, float]:
    f = {
        # auxiliary (not a model input): trusted tier-1/2 support exists
        "support_t12": 1.0 if any(e.locked and e.stance == "supports" and e.tier <= 2 for e in alibi.evidence) else 0.0,
        "contra_sources": float(len(alibi.contradict_domains)),   # auxiliary: independent contradicting sources
        "contradicted_t12": 1.0 if alibi.contradict_tier12 else 0.0,
        "contradicted_other": 1.0 if (alibi.contradict_other and not alibi.contradict_tier12) else 0.0,
        "support": support_score(alibi),
        "type_risk": TYPE_RISK.get(claim.type, 0.3),
    }
    if rei.status == "ok" and rei.answers:
        f["inconsistency"] = 1.0 - rei.agree_share
        f["witness_contradict"] = rei.contradict_share
    else:
        f["inconsistency"], f["witness_contradict"] = NEUTRAL["inconsistency"], NEUTRAL["witness_contradict"]
    f["phantom_bluff"] = ph.bluff if ph.status == "ok" else NEUTRAL["phantom_bluff"]
    f["tail_risk"] = fame.tail_risk if fame.status == "ok" else NEUTRAL["tail_risk"]
    f["citation_failure"] = max((failure_value(c.verdict) for c in cits), default=0.0)
    return f


def probability(f: dict[str, float], w: dict[str, float] | None = None) -> float:
    w = w or load_weights()[0]
    z = w["bias"] + sum(w[k] * f.get(k, 0.0) for k in FEATURES)
    return 1.0 / (1.0 + math.exp(-z))


def label_for(p: float, f: dict[str, float]) -> str:
    """Labels are tied to evidence, not only to the number: ❌ always has a locked contradicting
    quote, ✅ always has locked support. High risk without proof is 🟠 'suspicious'."""
    strong_contra = f.get("contradicted_t12", 0) > 0
    weak_contra = f.get("contradicted_other", 0) > 0
    trusted_support = f.get("support_t12", 0) > 0
    any_support = f.get("support", 0) > 0
    # A contradiction only wins if it is not outweighed by equally/more trusted support:
    # tier-1/2 vs tier-1/2 = "sources disagree"; a weak site can't overrule trusted support.
    # One lone contradicting source vs. witnesses who unanimously agree with the claim: don't call it false.
    lone_vs_witnesses = f.get("contra_sources", 0) <= 1 and f.get("inconsistency", 1) <= 0.2 \
        and f.get("witness_contradict", 0) == 0
    if p >= CONTRADICTED_MIN and not lone_vs_witnesses and \
            ((strong_contra and not trusted_support) or (weak_contra and not any_support)):
        return "contradicted"
    if any_support and p < CONFIRMED_MAX and not strong_contra:
        return "confirmed"
    if disputed(f):
        return "unconfirmed"
    if p >= SUSPICIOUS_MIN or f.get("citation_failure", 0) >= 1.0:
        return "suspicious"
    return "unconfirmed"


def disputed(f: dict[str, float]) -> bool:
    """Trusted sources on both sides, or trusted support against a weaker contradiction."""
    contra = f.get("contradicted_t12", 0) > 0 or f.get("contradicted_other", 0) > 0
    lone_vs_witnesses = f.get("contra_sources", 0) <= 1 and f.get("inconsistency", 1) <= 0.2 \
        and f.get("witness_contradict", 0) == 0
    return contra and (f.get("support", 0) > 0 or lone_vs_witnesses)


def contributions(f: dict[str, float], w: dict[str, float] | None = None) -> dict[str, float]:
    """How much each feature pushed the score (w·x), for the 'why' view and for debugging."""
    w = w or load_weights()[0]
    return {k: round(w[k] * f.get(k, 0.0), 3) for k in FEATURES}
