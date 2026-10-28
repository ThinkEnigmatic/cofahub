"""Himawari imagery adapter tests (offline URL construction)."""

from __future__ import annotations

from datetime import UTC, datetime

from cofa_forward.ingestion.himawari import latest_time, tile_url


def test_latest_time_is_ten_minute_multiple():
    t = latest_time()
    assert t.minute % 10 == 0
    assert t.second == 0
    assert t.tzinfo is not None


def test_tile_url_format():
    t = datetime(2026, 10, 28, 12, 50, 0, tzinfo=UTC)
    url = tile_url("1d", 550, t, 0, 0)
    assert url == "https://himawari8.nict.go.jp/img/D531106/1d/550/2026/10/28/125000_0_0.png"


def test_tile_url_full_disk_region():
    t = datetime(2026, 10, 28, 12, 50, 0, tzinfo=UTC)
    url = tile_url("4d", 550, t, 0, 0)
    assert "4d" in url and "125000_0_0.png" in url
