"""IBTrACS adapter tests (offline parse of a fixture + mocked fetch)."""

from __future__ import annotations

from pathlib import Path

from cofa_forward.ingestion.base import FetchResult
from cofa_forward.ingestion.ibtracs import FAS_BBOX, IbtracsAdapter, filter_bbox, parse_ibtracs

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "ibtracs_wp_sample.csv"


def test_parse_ibtracs_fixture():
    df = parse_ibtracs(FIXTURE)
    assert len(df) == 4
    assert set(df.columns) >= {"storm_id", "time", "lat", "lon", "wind_kt", "pressure_hpa"}
    assert df.iloc[0]["storm_id"] == "2020001N06131"
    assert df.iloc[0]["wind_kt"] == 30.0  # WMO_WIND
    assert df.iloc[0]["usa_wind_kt"] == 35.0
    assert df.iloc[0]["jma_wind_kt"] == 30.0
    assert df.iloc[0]["time"].tz is not None


def test_filter_bbox():
    df = parse_ibtracs(FIXTURE)
    sub = filter_bbox(df, **FAS_BBOX)
    # all fixture rows except the 175E one are inside FAS bbox
    assert len(sub) == 3
    assert "2020002N09175" not in sub["storm_id"].values


def test_get_tracks_mocked(monkeypatch):
    adapter = IbtracsAdapter()

    def fake_fetch(url, params=None, timeout=None):
        return FetchResult(True, "noaa-ibtracs", url, data=FIXTURE.read_text())

    monkeypatch.setattr(adapter, "fetch_text", fake_fetch)
    r = adapter.get_tracks(bbox=FAS_BBOX)
    assert r["ok"] is True
    assert r["n_points"] == 3
    assert r["n_storms"] == 1


def test_get_tracks_failure(monkeypatch):
    adapter = IbtracsAdapter()

    def fake_fetch(url, params=None, timeout=None):
        return FetchResult(False, "noaa-ibtracs", url, error="timeout")

    monkeypatch.setattr(adapter, "fetch_text", fake_fetch)
    r = adapter.get_tracks()
    assert r["ok"] is False
    assert r["error"] == "timeout"


def test_parse_ibtracs_handles_missing_agency_cols(tmp_path):
    # minimal CSV without USA_WIND/TOKYO_WIND columns
    p = tmp_path / "mini.csv"
    p.write_text(
        "SID,ISO_TIME,LAT,LON,WMO_WIND,WMO_PRES,WMO_AGENCY,BASIN\n"
        ",,,,,,,\n"
        "S1,2020-01-01 00:00:00,5.0,140.0,30,995,TOKYO,WP\n"
    )
    df = parse_ibtracs(p)
    assert len(df) == 1
    assert df.iloc[0]["storm_id"] == "S1"
    assert pd_isna(df.iloc[0]["usa_wind_kt"])


def pd_isna(v):
    import pandas as pd

    return pd.isna(v)
