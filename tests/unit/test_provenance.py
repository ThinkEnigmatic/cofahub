"""Provenance and storage tests."""

from __future__ import annotations

from cofa_forward.storage.cache import FileCache, cache_key
from cofa_forward.storage.database import Database
from cofa_forward.storage.provenance import build_provenance


def test_build_provenance_fields():
    p = build_provenance(
        dataset_id="d", source_url="u", calculation_method="m", parameters={"a": 1}
    )
    assert p["dataset_id"] == "d"
    assert p["source_url"] == "u"
    assert p["calculation_method"] == "m"
    assert p["parameters"] == {"a": 1}


def test_cache_key_deterministic_and_order_independent():
    assert cache_key("http://x", {"a": 1, "b": 2}) == cache_key("http://x", {"b": 2, "a": 1})
    assert cache_key("http://x", {"a": 1}) != cache_key("http://x", {"a": 2})


def test_file_cache_roundtrip(tmp_path):
    cache = FileCache(tmp_path, ttl_seconds=60)
    key = cache_key("http://x", {"q": 1})
    assert cache.get(key) is None
    cache.set_json(key, {"hello": "world"})
    assert cache.get_json(key) == {"hello": "world"}
    assert cache.get(key) is not None


def test_file_cache_expiry(tmp_path):
    import time

    cache = FileCache(tmp_path, ttl_seconds=0)  # immediately expired
    key = cache_key("http://x")
    cache.set_json(key, {"a": 1})
    time.sleep(0.01)
    assert cache.get(key) is None


def test_database_provenance_roundtrip(tmp_path):
    db = Database(tmp_path / "catalog.db")
    db.insert_provenance(build_provenance(dataset_id="d", notes="n"))
    rows = db.query("SELECT dataset_id, notes FROM provenance")
    assert rows and rows[0]["dataset_id"] == "d"
    db.record_ingestion("open-meteo-forecast", "ok", "test")
    hist = db.query("SELECT source_id, status FROM ingestion_history")
    assert hist and hist[0]["source_id"] == "open-meteo-forecast"
    db.close()
