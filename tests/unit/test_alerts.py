"""Alert threshold evaluation tests."""

from __future__ import annotations

import pytest

from cofa_forward.drought.alerts import evaluate_alerts, evaluate_threshold
from cofa_forward.schemas import AlertThreshold


def _t(operator, value):
    return AlertThreshold(
        id="x", name="x", indicator="i", threshold={"operator": operator, "value": value}
    )


def test_gt():
    assert evaluate_threshold(_t("gt", 100.0), 150.0) is True
    assert evaluate_threshold(_t("gt", 100.0), 50.0) is False


def test_lt():
    assert evaluate_threshold(_t("lt", 0.2), 0.1) is True
    assert evaluate_threshold(_t("lt", 0.2), 0.5) is False


def test_nan_never_fires():
    assert evaluate_threshold(_t("gt", 100.0), float("nan")) is False


def test_unsupported_operator():
    with pytest.raises(ValueError):
        evaluate_threshold(_t("wat", 1.0), 2.0)


def test_evaluate_alerts():
    thresholds = [
        AlertThreshold(id="a", name="a", indicator="p", threshold={"operator": "lt", "value": 0.2})
    ]
    results = evaluate_alerts(thresholds, {"p": 0.1})
    assert results[0]["fired"] is True
    assert results[0]["value"] == 0.1
