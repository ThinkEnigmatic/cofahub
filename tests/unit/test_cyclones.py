"""Cyclone proximity / tracks / exposure / ENSO-analysis tests."""

from __future__ import annotations

import pandas as pd

from cofa_forward.cyclones.climatology import seasonal_summary
from cofa_forward.cyclones.enso_analysis import phase_storm_counts
from cofa_forward.cyclones.exposure import exposed_locations
from cofa_forward.cyclones.proximity import closest_approach, within_radius
from cofa_forward.cyclones.tracks import storm_count_by_year, validate_track_df


def _track() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "storm_id": "S1",
                "time": pd.Timestamp("2020-01-01"),
                "lat": 5.0,
                "lon": 150.0,
                "wind_kt": 60.0,
                "pressure_hpa": 985.0,
                "agency": "TEST",
            },
            {
                "storm_id": "S1",
                "time": pd.Timestamp("2020-01-02"),
                "lat": 7.0,
                "lon": 152.0,
                "wind_kt": 80.0,
                "pressure_hpa": 970.0,
                "agency": "TEST",
            },
            {
                "storm_id": "S2",
                "time": pd.Timestamp("2020-06-01"),
                "lat": 8.0,
                "lon": 170.0,
                "wind_kt": 40.0,
                "pressure_hpa": 995.0,
                "agency": "TEST",
            },
        ]
    )


def test_validate_track_df():
    assert validate_track_df(_track()) is not None
    import pytest

    with pytest.raises(ValueError):
        validate_track_df(pd.DataFrame({"x": [1]}))


def test_closest_approach():
    # point near the first track point
    ca = closest_approach(5.0, 150.0, _track())
    assert ca["distance_km"] < 5.0
    assert ca["time"] == pd.Timestamp("2020-01-01")


def test_closest_approach_non_default_index():
    # regression: groupby subsets carry original (non-zero-based) labels
    df = _track().reset_index(drop=True)
    sub = df[df["storm_id"] == "S2"]  # label 2 only
    ca = closest_approach(8.0, 170.0, sub)
    assert ca["distance_km"] < 5.0


def test_within_radius():
    sub = within_radius(5.0, 150.0, _track(), 50.0)
    assert len(sub) == 1
    assert sub.iloc[0]["storm_id"] == "S1"


def test_storm_count_by_year():
    counts = storm_count_by_year(_track())
    assert counts[2020] == 2


def test_seasonal_summary():
    s = seasonal_summary(_track())
    assert s["n_storms"] == 2
    assert s["n_points"] == 3


def test_exposed_locations(registry):
    exp = exposed_locations(registry, _track(), 50.0)
    assert isinstance(exp, list)


def test_phase_storm_counts():
    events = pd.DataFrame(
        [
            {"storm_id": "S1", "enso_phase": "el_nino"},
            {"storm_id": "S2", "enso_phase": "la_nina"},
            {"storm_id": "S3", "enso_phase": "el_nino"},
        ]
    )
    res = phase_storm_counts(events)
    assert res["storm_counts"] == {"el_nino": 2, "la_nina": 1}
    assert res["n_total_storms"] == 3
