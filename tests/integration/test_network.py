"""Live network integration tests (marked ``network``; skipped by default).

Run explicitly with:  uv run pytest -m network
"""

from __future__ import annotations

import pytest

from cofa_forward.config import get_config
from cofa_forward.ingestion.enso import CpcOniAdapter
from cofa_forward.ingestion.ibtracs import FAS_BBOX, IbtracsAdapter
from cofa_forward.ingestion.jma import JmaTyphoonAdapter
from cofa_forward.ingestion.rainfall import OpenMeteoArchiveAdapter
from cofa_forward.ingestion.weather import OpenMeteoForecastAdapter

pytestmark = pytest.mark.network


def test_live_forecast():
    cfg = get_config()
    adapter = OpenMeteoForecastAdapter(config=cfg)
    r = adapter.get_forecast(7.342, 134.478, forecast_days=7)
    assert r["ok"], f"live forecast failed: {r.get('error')}"
    assert len(r["hourly"]) > 0
    assert "temperature_2m" in r["hourly"].columns


def test_live_model_comparison():
    cfg = get_config()
    adapter = OpenMeteoForecastAdapter(config=cfg)
    r = adapter.get_model_comparison(7.342, 134.478, variable="temperature_2m")
    assert r["ok"], f"live model comparison failed: {r.get('error')}"
    assert r["n_models"] >= 3
    assert "best_match" in r["models"].columns


def test_live_archive_rainfall():
    cfg = get_config()
    adapter = OpenMeteoArchiveAdapter(config=cfg)
    r = adapter.get_rainfall(7.342, 134.478, "2023-01-01", "2023-12-31")
    assert r["ok"], f"live archive failed: {r.get('error')}"
    assert r["n_days"] >= 350


def test_live_oni():
    adapter = CpcOniAdapter()
    r = adapter.get_oni()
    assert r["ok"], f"live ONI failed: {r.get('error')}"
    assert r["latest"]["anom"] != 0.0
    assert r["phase"] in ("el_nino", "la_nina", "neutral")
    assert len(r["series"]) > 900  # 1950 -> present


def test_live_jma_active_storms():
    adapter = JmaTyphoonAdapter()
    r = adapter.active_storms()
    assert r["ok"], f"live JMA failed: {r.get('error')}"
    assert r["n_active"] >= 0
    # if there is an active storm, its details must be fetchable
    for storm in r["storms"][:2]:
        d = adapter.storm_details(storm["tc_id"])
        assert d["ok"], f"JMA storm details failed: {d.get('error')}"
        assert d["analysis"].get("position") is not None


def test_live_ibtracs_fas_tracks():
    adapter = IbtracsAdapter()
    r = adapter.get_tracks(bbox=FAS_BBOX)
    assert r["ok"], f"live IBTrACS failed: {r.get('error')}"
    assert r["n_storms"] > 0
    assert r["n_points"] > 0


def test_live_imerg_daily():
    from cofa_forward.ingestion.imerg import ImergAdapter

    adapter = ImergAdapter()
    # V07 Final daily extends through ~Sep 2025; use a safe historical window.
    r = adapter.get_recent_daily(7.34, 134.48, "2025-06-01", "2025-06-03")
    assert r["ok"], f"live IMERG failed: {r.get('error')}"
    assert r["n_days"] == 3
    assert r["series"].notna().all()


def test_live_jtwc_warning():
    from cofa_forward.ingestion.jtwc import JtwcAdapter

    adapter = JtwcAdapter()
    r = adapter.get_active_warnings()
    assert r["ok"], f"live JTWC failed: {r.get('errors')}"
    # If there are active storms, the parse must have produced identities.
    for w in r["storms"]:
        assert w.get("storm_id")
        assert w.get("name")
        assert w.get("position") is not None


def test_live_himawari_image():
    import requests

    from cofa_forward.ingestion.himawari import HimawariAdapter

    r = HimawariAdapter().latest_full_disk()
    assert r["ok"]
    resp = requests.head(r["image_url"], timeout=20)
    assert resp.status_code == 200, f"Himawari tile returned {resp.status_code}"


def test_live_nws_guam_advisory():
    from cofa_forward.ingestion.nws_guam import NwsGuamAdapter

    r = NwsGuamAdapter().get_advisory()
    assert r["ok"], f"live NWS Guam failed: {r.get('error')}"
    assert r.get("agency") == "PGUM"


def test_live_peac_outlook():
    from cofa_forward.ingestion.peac import PeacRainfallOutlookAdapter

    r = PeacRainfallOutlookAdapter().get_outlook()
    assert r["ok"], f"live PEAC failed: {r.get('error')}"
    assert r.get("season_label")
    assert r.get("last_updated")
    assert r.get("is_stale") is True  # known-stale product (last updated 2024-09-16)
    fas = [s for s in r["stations"] if s["geo_id"]]
    assert len(fas) == 7  # Koror, Yap, Chuuk, Pohnpei, Kosrae, Kwajalein, Majuro
    for s in fas:
        assert s["final_outlook"]
        assert s["probabilities"].count(":") == 2
