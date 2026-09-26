"""Metrics and a tiny dependency-free logistic regression (≈200 labeled claims don't need scikit-learn)."""

from __future__ import annotations

import math
import random


def prf(gold: list[int], pred: list[int]) -> dict[str, float]:
    """Precision / recall / F1 for the positive class (1 = "the claim is FALSE"), plus accuracy."""
    tp = sum(g == 1 and p == 1 for g, p in zip(gold, pred))
    fp = sum(g == 0 and p == 1 for g, p in zip(gold, pred))
    fn = sum(g == 1 and p == 0 for g, p in zip(gold, pred))
    correct = sum(g == p for g, p in zip(gold, pred))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
            "accuracy": round(correct / len(gold), 3) if gold else 0.0, "n": len(gold)}


def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-35.0, min(35.0, z))))


def fit_logreg(X: list[list[float]], y: list[int], l2: float = 0.05, lr: float = 0.3,
               epochs: int = 3000) -> tuple[float, list[float]]:
    """Batch gradient descent with L2 regularization. Returns (bias, weights)."""
    n, d = len(X), len(X[0])
    b, w = 0.0, [0.0] * d
    for _ in range(epochs):
        gb, gw = 0.0, [0.0] * d
        for xi, yi in zip(X, y):
            err = _sigmoid(b + sum(wj * xj for wj, xj in zip(w, xi))) - yi
            gb += err
            for j in range(d):
                gw[j] += err * xi[j]
        b -= lr * gb / n
        w = [wj - lr * (gwj / n + l2 * wj) for wj, gwj in zip(w, gw)]
    return b, w


def predict(b: float, w: list[float], x: list[float]) -> float:
    return _sigmoid(b + sum(wj * xj for wj, xj in zip(w, x)))


def cross_validate(X, y, k: int = 5, seed: int = 7, **fit_kw) -> dict[str, float]:
    idx = list(range(len(X)))
    random.Random(seed).shuffle(idx)
    folds = [idx[i::k] for i in range(k)]
    gold, pred = [], []
    for f in folds:
        if not f:
            continue
        test = set(f)
        Xtr = [X[i] for i in idx if i not in test]
        ytr = [y[i] for i in idx if i not in test]
        if len(set(ytr)) < 2:
            continue
        b, w = fit_logreg(Xtr, ytr, **fit_kw)
        for i in f:
            gold.append(y[i])
            pred.append(1 if predict(b, w, X[i]) >= 0.5 else 0)
    return prf(gold, pred)
