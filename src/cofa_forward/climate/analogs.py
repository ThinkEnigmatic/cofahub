"""Historical analog engine.

Analogs are selected with an explainable, deterministic numeric similarity —
NOT a language-model-generated score. Each feature contributes a documented,
normalized distance; missing features are excluded and reported. A historical
analog is contextual evidence, not a forecast.
"""

from __future__ import annotations

from typing import Any


def _norm_diff(a: float, b: float, scale: float) -> float:
    """Normalized absolute difference clamped to [0, 1]."""
    if scale <= 0:
        return 0.0
    return min(1.0, abs(a - b) / scale)


def similarity(
    current: dict[str, float],
    candidate: dict[str, float],
    weights: dict[str, float],
    scales: dict[str, float],
) -> tuple[float, dict[str, Any]]:
    """Weighted similarity in [0, 1] (1 = identical) plus per-feature breakdown.

    Features missing from either side are skipped and listed in ``missing``.
    """
    total_w = 0.0
    weighted_dist = 0.0
    per_feature: dict[str, float] = {}
    missing: list[str] = []

    for feature, w in weights.items():
        if w <= 0:
            continue
        cv = current.get(feature)
        cc = candidate.get(feature)
        if cv is None or cc is None:
            missing.append(feature)
            continue
        scale = scales.get(feature, 1.0)
        d = _norm_diff(cv, cc, scale)
        per_feature[feature] = d
        weighted_dist += w * d
        total_w += w

    if total_w == 0:
        return 0.0, {
            "per_feature": per_feature,
            "missing": missing,
            "note": "no comparable features",
        }

    score = 1.0 - (weighted_dist / total_w)
    return score, {"per_feature": per_feature, "missing": missing}


def rank_analogs(
    current: dict[str, float],
    candidates: list[dict[str, Any]],
    weights: dict[str, float],
    scales: dict[str, float],
) -> list[dict[str, Any]]:
    """Rank candidate analogs by similarity to ``current``.

    ``candidates`` is a list of dicts each having an ``id`` key and numeric
    feature keys. Returns candidates enriched with ``similarity`` and
    ``explanation``, sorted descending by similarity.
    """
    ranked = []
    for cand in candidates:
        cand_id = cand.get("id")
        features = {k: v for k, v in cand.items() if k != "id" and isinstance(v, (int, float))}
        sim, detail = similarity(current, features, weights, scales)
        ranked.append(
            {
                "id": cand_id,
                "similarity": sim,
                "per_feature": detail["per_feature"],
                "missing": detail["missing"],
            }
        )
    ranked.sort(key=lambda r: r["similarity"], reverse=True)
    return ranked
