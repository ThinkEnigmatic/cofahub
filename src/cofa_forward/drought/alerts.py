"""Analyst-defined alert threshold evaluation.

Thresholds are internal watch levels, NOT official government warnings. Each
evaluation returns the threshold, the observed value, and whether it fired.
"""

from __future__ import annotations

from typing import Any

from ..schemas import AlertThreshold


def evaluate_threshold(threshold: AlertThreshold, value: float) -> bool:
    """Evaluate a single threshold against a scalar indicator value."""
    spec = threshold.threshold
    op = spec.get("operator", "gt")
    limit = spec.get("value")
    if limit is None or (isinstance(value, float) and value != value):  # NaN
        return False
    if op == "gt":
        return value > limit
    if op == "lt":
        return value < limit
    if op == "gte":
        return value >= limit
    if op == "lte":
        return value <= limit
    if op == "eq":
        return value == limit
    raise ValueError(f"Unsupported threshold operator: {op}")


def evaluate_alerts(
    thresholds: list[AlertThreshold],
    indicators: dict[str, float],
) -> list[dict[str, Any]]:
    """Evaluate all thresholds against a dict of indicator values.

    Returns a list of result dicts with ``id``, ``name``, ``fired``,
    ``value``, ``threshold``, and ``note``.
    """
    results: list[dict[str, Any]] = []
    for t in thresholds:
        value = indicators.get(t.indicator, float("nan"))
        fired = evaluate_threshold(t, value)
        results.append(
            {
                "id": t.id,
                "name": t.name,
                "indicator": t.indicator,
                "value": value,
                "fired": fired,
                "threshold": t.threshold,
                "note": t.note,
            }
        )
    return results
