"""Offline snapshot store and mode detection.

COFA FORWARD can run against a pre-fetched *snapshot* of its live sources so the
macOS app (and any other deployment) works without a network connection. The
snapshot is a directory of per-source JSON/Parquet files plus a ``manifest.json``
that records what was captured and when.

Mode is selected with the ``COFA_OFFLINE`` environment variable (``1``/``true``/
``yes``/``on``). When offline:

* the file cache serves stale entries (never expires), and
* the UI surfaces the snapshot age instead of live timestamps.

The snapshot is produced by ``scripts/prefetch_snapshot.py`` (run when online)
and read by the UI fallbacks. Nothing here fabricates data: a source that was not
successfully captured is simply absent from the manifest and reported missing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

_MANIFEST = "manifest.json"


def is_offline() -> bool:
    """True when COFA_OFFLINE is set to a truthy value."""
    v = os.environ.get("COFA_OFFLINE", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def snapshot_dir(config=None) -> Path:
    """Resolve the snapshot directory (env override or ``<data_root>/snapshot``)."""
    override = os.environ.get("COFA_SNAPSHOT_DIR")
    if override:
        return Path(override)
    if config is not None:
        return config.data_root / "snapshot"
    return Path("data/snapshot")


class SnapshotStore:
    """Read/write a per-source offline snapshot plus a manifest."""

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _manifest_path(self) -> Path:
        return self.directory / _MANIFEST

    def write(self, source_id: str, data: Any, *, written_at: str | None = None) -> Path:
        """Write a JSON-serializable payload and record it in the manifest."""
        path = self.directory / f"{source_id}.json"
        path.write_text(json.dumps(data, default=str, ensure_ascii=False), encoding="utf-8")
        self._touch(source_id, file=path.name, written_at=written_at)
        return path

    def read(self, source_id: str) -> Any | None:
        path = self.directory / f"{source_id}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None

    def write_df(self, source_id: str, df: pd.DataFrame, *, written_at: str | None = None) -> Path:
        """Write a DataFrame as Parquet and record it in the manifest."""
        path = self.directory / f"{source_id}.parquet"
        df.to_parquet(path, index=False)
        self._touch(source_id, file=path.name, written_at=written_at)
        return path

    def read_df(self, source_id: str) -> pd.DataFrame | None:
        path = self.directory / f"{source_id}.parquet"
        if not path.exists():
            return None
        try:
            return pd.read_parquet(path)
        except Exception:  # noqa: BLE001 - a corrupt snapshot is treated as missing
            return None

    def mark_missing(self, source_id: str, reason: str, *, written_at: str | None = None) -> None:
        """Record that a source could not be captured (so the UI can say so honestly)."""
        self._touch(source_id, ok=False, reason=reason, written_at=written_at)

    def _touch(
        self,
        source_id: str,
        *,
        file: str | None = None,
        ok: bool = True,
        reason: str | None = None,
        written_at: str | None = None,
    ) -> None:
        manifest = self.manifest()
        entry: dict[str, Any] = {
            "written_at": written_at or _now_iso(),
            "ok": ok,
        }
        if file:
            entry["file"] = file
        if reason:
            entry["reason"] = reason
        manifest["sources"][source_id] = entry
        manifest["snapshot_at"] = manifest.get("snapshot_at") or entry["written_at"]
        self._manifest_path().write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def manifest(self) -> dict[str, Any]:
        path = self._manifest_path()
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                pass
        return {"snapshot_at": None, "sources": {}}

    def available(self, source_id: str) -> bool:
        entry = self.manifest().get("sources", {}).get(source_id)
        return bool(entry and entry.get("ok"))


def _now_iso() -> str:
    from ..timeutil import format_iso, now_utc

    return format_iso(now_utc())
