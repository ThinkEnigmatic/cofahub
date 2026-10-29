"""Offline snapshot store + serve-stale cache tests (offline)."""

from __future__ import annotations

import pandas as pd

from cofa_forward.storage.cache import FileCache
from cofa_forward.storage.snapshot import SnapshotStore, is_offline


def test_is_offline_flag(monkeypatch):
    monkeypatch.setenv("COFA_OFFLINE", "1")
    assert is_offline() is True
    monkeypatch.setenv("COFA_OFFLINE", "true")
    assert is_offline() is True
    monkeypatch.delenv("COFA_OFFLINE")
    assert is_offline() is False
    monkeypatch.setenv("COFA_OFFLINE", "0")
    assert is_offline() is False


def test_snapshot_store_json_roundtrip(tmp_path):
    store = SnapshotStore(tmp_path)
    store.write("enso_oni", {"phase": "el_nino", "anom": 2.1})
    assert store.read("enso_oni")["phase"] == "el_nino"
    assert store.available("enso_oni")
    m = store.manifest()
    assert m["sources"]["enso_oni"]["ok"] is True
    assert m["snapshot_at"] is not None


def test_snapshot_store_df_roundtrip(tmp_path):
    store = SnapshotStore(tmp_path)
    df = pd.DataFrame(
        {"date": pd.to_datetime(["2024-01-01", "2024-02-01"]), "precip_mm": [10.0, 20.0]}
    )
    store.write_df("rainfall_RMI-MAJ", df)
    back = store.read_df("rainfall_RMI-MAJ")
    assert list(back["precip_mm"]) == [10.0, 20.0]


def test_snapshot_store_missing(tmp_path):
    store = SnapshotStore(tmp_path)
    store.mark_missing("himawari_latest", "network error")
    assert not store.available("himawari_latest")
    assert store.read("himawari_latest") is None
    assert "himawari_latest" in store.manifest()["sources"]


def test_snapshot_read_missing_returns_none(tmp_path):
    store = SnapshotStore(tmp_path)
    assert store.read("nonexistent") is None
    assert store.read_df("nonexistent") is None


def test_file_cache_serve_stale(tmp_path):
    c = FileCache(tmp_path, ttl_seconds=0, serve_stale=True)
    c.set("k", b"v")
    assert c.get("k") == b"v"  # ttl=0 but serve_stale keeps it


def test_file_cache_expires_without_serve_stale(tmp_path):
    c = FileCache(tmp_path, ttl_seconds=0, serve_stale=False)
    c.set("k", b"v")
    assert c.get("k") is None
