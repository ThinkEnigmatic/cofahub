"""File-based cache with TTL.

Reproducible, keys by a SHA-256 of (url + canonical params). Stores the raw
bytes so any adapter can cache its own serialization format.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


def cache_key(url: str, params: dict[str, Any] | None = None) -> str:
    """Deterministic cache key from a URL and (optionally) canonical params."""
    params = params or {}
    canonical = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha256(f"{url}|{canonical}".encode()).hexdigest()
    return digest


class FileCache:
    """TTL cache writing raw bytes under a cache directory."""

    def __init__(self, cache_dir: Path | str, ttl_seconds: int = 900):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = int(ttl_seconds)

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> bytes | None:
        p = self._path(key)
        if not p.exists():
            return None
        age = time.time() - p.stat().st_mtime
        if age > self.ttl_seconds:
            return None
        return p.read_bytes()

    def set(self, key: str, data: bytes) -> None:
        self._path(key).write_bytes(data)

    def get_json(self, key: str) -> Any | None:
        raw = self.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def set_json(self, key: str, data: Any) -> None:
        self.set(key, json.dumps(data, default=str).encode("utf-8"))

    def clear(self) -> None:
        for p in self.cache_dir.glob("*.json"):
            p.unlink(missing_ok=True)
