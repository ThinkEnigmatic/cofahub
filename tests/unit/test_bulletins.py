"""Bulletin monitor and parser tests."""

from __future__ import annotations

from cofa_forward.config import Config
from cofa_forward.ingestion.bulletins import (
    BulletinMonitor,
    parse_cpc_enso_html,
    parse_jma_info,
    parse_wmo_text,
    summarize,
)
from cofa_forward.storage.database import Database


def test_parse_wmo_text():
    text = (
        "WTPQ31 PGUM 281200\nTCPPQ1\n\nBULLETIN\nPUBLIC TROPICAL CYCLONE ADVISORY\nNWS TIYAN GUAM\n"
    )
    s = parse_wmo_text(text)
    assert s["header"] == "WTPQ31"
    assert s["agency"] == "PGUM"
    assert s["issue_time"] == "281200"
    assert "ADVISORY" in s["headline"].upper()


def test_parse_jma_info():
    data = [
        {
            "headTitle": "台風第6号",
            "reportDatetime": "2026-05-27T10:30:00+09:00",
            "eventId": "TC2606",
            "infoType": "発表",
            "header": "VPTI51",
            "datetime": "2026-05-27T01:25:17Z",
        },
        {
            "headTitle": "台風第7号",
            "reportDatetime": "2026-05-28T10:30:00+09:00",
            "eventId": "TC2607",
            "infoType": "発表",
            "header": "VPTI51",
            "datetime": "2026-05-28T01:25:17Z",
        },
    ]
    s = parse_jma_info(data)
    assert s["n_bulletins"] == 2
    assert s["latest_event_id"] == "TC2607"


def test_parse_cpc_enso_html():
    html = "<html><body>ENSO Alert System Status: El Ni&ntilde;o Advisory "
    html += "Synopsis: El Ni&ntilde;o continues to strengthen.</p>"
    html += "<p>last modified 8 October 2026</p></body></html>"
    s = parse_cpc_enso_html(html)
    assert s["enso_alert_status"] == "El Niño Advisory"
    assert s["last_modified"] == "8 October 2026"


def test_summarize_dispatch():
    assert summarize("jma_info", [])["n_bulletins"] == 0
    assert summarize("unknown_kind", "x") == {"note": "no parser for kind 'unknown_kind'"}


class _FakeFetcher:
    def __init__(self, data, ok=True, error=None):
        self.data = data
        self.ok = ok
        self.error = error
        self.retrieved_at = "2026-10-28T00:00:00Z"


def test_monitor_first_check_is_update(tmp_path):
    cfg = Config()  # real config (bulletins.yaml present)
    db = Database(tmp_path / "catalog.db")

    monitor = BulletinMonitor(cfg, db=db)
    source = {"id": "test", "name": "Test", "url": "http://x", "kind": "wmo_text"}
    monitor._fetch = lambda s: _FakeFetcher(
        "WTPQ31 PGUM 281200\nPUBLIC TROPICAL CYCLONE ADVISORY\n"
    )

    r1 = monitor.check(source)
    assert r1["ok"] is True
    assert r1["changed"] is True
    assert "ADVISORY" in r1["summary"]["headline"].upper()

    # second identical check -> no change
    r2 = monitor.check(source)
    assert r2["changed"] is False

    # changed content -> update again
    monitor._fetch = lambda s: _FakeFetcher(
        "WTPQ31 PGUM 281200\nPUBLIC TROPICAL CYCLONE ADVISORY\nCHANGED\n"
    )
    r3 = monitor.check(source)
    assert r3["changed"] is True

    # update log has two entries
    recent = db.recent_bulletins()
    assert len(recent) == 2


def test_monitor_fetch_error(tmp_path):
    cfg = Config()
    db = Database(tmp_path / "catalog.db")
    monitor = BulletinMonitor(cfg, db=db)
    monitor._fetch = lambda s: _FakeFetcher(None, ok=False, error="down")
    r = monitor.check({"id": "x", "name": "X", "url": "http://x", "kind": "wmo_text"})
    assert r["ok"] is False
    assert r["changed"] is False
    assert r["error"] == "down"
