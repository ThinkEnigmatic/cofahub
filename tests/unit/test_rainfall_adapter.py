"""Open-Meteo archive (rainfall) adapter tests (offline)."""

from __future__ import annotations

import pytest

from cofa_forward.ingestion.rainfall import OpenMeteoArchiveAdapter, normalize_archive_rainfall


def test_normalize_archive_rainfall():
    payload = {"daily": {"time": ["2026-10-27", "2026-10-28"], "precipitation_sum": [1.5, 2.5]}}
    s = normalize_archive_rainfall(payload)
    assert list(s.values) == [1.5, 2.5]
    assert s.index.tz is not None
    assert s.name == "precip_mm"


def test_normalize_archive_missing_raises():
    with pytest.raises(ValueError):
        normalize_archive_rainfall({"daily": {"precipitation_sum": [1.0]}})


def test_get_rainfall_failure(monkeypatch):
    from cofa_forward.ingestion.base import FetchResult

    adapter = OpenMeteoArchiveAdapter()

    def fake_fetch(url, params=None, timeout=None):
        return FetchResult(False, "open-meteo-archive", url, error="timeout")

    monkeypatch.setattr(adapter, "fetch_json", fake_fetch)
    r = adapter.get_rainfall(7.34, 134.48, "2020-01-01", "2020-12-31")
    assert r["ok"] is False
    assert r["error"] == "timeout"
