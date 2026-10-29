"""UHSLC tide-gauge adapter tests (offline)."""

from __future__ import annotations

from cofa_forward.ingestion.uhslc import FAS_GAUGES, UhslcAdapter, query_url


def test_fas_gauges_mapping():
    assert "RMI-MAJ" in FAS_GAUGES
    assert "PAL-KOR" in FAS_GAUGES
    assert FAS_GAUGES["RMI-MAJ"] == "Majuro"
    assert FAS_GAUGES["PAL-KOR"] == "Malakal"  # Palau's tide gauge
    assert len(FAS_GAUGES) == 6


def test_query_url_shape():
    url = query_url("Majuro", "2024-06-01", "2024-06-02")
    assert url.startswith("https://uhslc.soest.hawaii.edu/erddap/tabledap/global_hourly_fast.csv?")
    assert "station_name=%22Majuro%22" in url  # ERDDAP requires quoted strings
    assert "time>=" in url and "time<=" in url


def test_adapter_id():
    assert UhslcAdapter().source_id == "uhslc-tide-gauge"
