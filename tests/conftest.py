"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.config import get_config  # noqa: E402
from cofa_forward.geography.registry import GeographyRegistry  # noqa: E402


@pytest.fixture(scope="session")
def config():
    return get_config()


@pytest.fixture(scope="session")
def registry(config) -> GeographyRegistry:
    return GeographyRegistry(config.geography_entities())


def make_daily(values: dict[str, float], days_per_month: dict[str, int] | None = None) -> pd.Series:
    """Build a daily rainfall series from explicit month -> total values.

    Each month is spread evenly across its days so totals are exact. Defaults to
    standard month lengths.
    """
    days_per_month = days_per_month or {
        "2020-01": 31,
        "2020-02": 29,
        "2020-03": 31,
        "2020-04": 30,
        "2020-05": 31,
        "2020-06": 30,
    }
    rows = []
    for ym, total in values.items():
        n = days_per_month[ym]
        for d in range(1, n + 1):
            ts = pd.Timestamp(f"{ym}-{d:02d}")
            rows.append((ts, total / n))
    idx = pd.DatetimeIndex([r[0] for r in rows])
    return pd.Series([r[1] for r in rows], index=idx, name="precip_mm")
