"""El Niño comparison + crisis-history tests (offline)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cofa_forward.drought.el_nino_comparison import (
    build_comparison,
    rolling_anomaly_pct,
)
from cofa_forward.drought.el_nino_history import (
    CRISIS,
    EL_NINO_EVENTS,
    LAST_MAJOR_EMERGENCY,
    REGIONAL_NOTE,
)


def _synthetic_daily() -> pd.Series:
    idx = pd.date_range("1997-01-01", "2026-10-29", freq="D")
    rng = np.random.default_rng(0)
    seasonal = 6 + 4 * np.sin(2 * np.pi * (idx.day_of_year) / 365 + 2.0)
    s = pd.Series(seasonal + rng.gamma(1.0, 1.0, len(idx)), index=idx, name="precip_mm")
    return s


def test_build_comparison_shape():
    c = build_comparison(_synthetic_daily())
    assert set(c["events"]) == {e["id"] for e in EL_NINO_EVENTS}
    assert len(c["climatology"]) == 12
    assert c["current"]["label"] == "Current cycle"
    assert len(c["current"]["monthly"]) <= 24


def test_rolling_anomaly_is_percent_of_normal():
    idx = pd.date_range("2000-01-01", "2003-12-01", freq="MS")
    monthly = pd.Series([100.0] * len(idx), index=idx)
    climatology = pd.Series([100.0] * 12, index=range(1, 13))
    anom = rolling_anomaly_pct(monthly, climatology, window=6)
    assert anom.dropna().round(0).eq(100.0).all()


def test_rolling_anomaly_handles_dry_spell():
    idx = pd.date_range("2000-01-01", "2003-12-01", freq="MS")
    vals = [10.0] * len(idx)  # only 10% of a 100 mm normal
    monthly = pd.Series(vals, index=idx)
    climatology = pd.Series([100.0] * 12, index=range(1, 13))
    anom = rolling_anomaly_pct(monthly, climatology, window=6)
    assert (anom.dropna().round(0) == 10.0).all()


def test_crisis_history_has_last_major_emergency_per_country():
    for geo_id in ("RMI", "FSM", "PAL"):
        assert geo_id in CRISIS
        assert LAST_MAJOR_EMERGENCY in CRISIS[geo_id]
        assert CRISIS[geo_id][LAST_MAJOR_EMERGENCY]["sources"]


def test_crisis_facts_all_have_sources():
    for geo_id, events in CRISIS.items():
        for ev_id, facts in events.items():
            assert facts.get("sources"), f"{geo_id}/{ev_id} missing sources"
            assert facts.get("emergency"), f"{geo_id}/{ev_id} missing emergency text"


def test_regional_note_present():
    assert REGIONAL_NOTE["summary"]
    assert REGIONAL_NOTE["sources"]
