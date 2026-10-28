"""SQLite-backed metadata store.

Holds provenance records, ingestion history, and (later) document index. Uses
the stdlib ``sqlite3`` so the base app has no heavy database dependency.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT,
    dataset_id TEXT,
    source_url TEXT,
    retrieved_at TEXT,
    valid_time TEXT,
    init_time TEXT,
    lead_time TEXT,
    calculation_method TEXT,
    parameters TEXT,
    baseline_period TEXT,
    geographic_aggregation TEXT,
    missing_data_handling TEXT,
    output_timestamp TEXT,
    code_version TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS ingestion_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT,
    status TEXT,
    message TEXT,
    retrieved_at TEXT,
    valid_time TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT,
    publisher TEXT,
    source_url TEXT,
    publication_date TEXT,
    event_dates TEXT,
    geographic_scope TEXT,
    hazard_categories TEXT,
    enso_episode TEXT,
    license TEXT,
    extraction_status TEXT,
    verification_status TEXT,
    passages TEXT,
    citation TEXT
);

CREATE INDEX IF NOT EXISTS idx_prov_dataset ON provenance(dataset_id);
CREATE INDEX IF NOT EXISTS idx_ingest_source ON ingestion_history(source_id);
"""


class Database:
    """Thread-safe wrapper around a single SQLite database file."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._conn = self._connect()
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    @property
    def conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._connect()
        return self._local.conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur

    def query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        cur = self.conn.execute(sql, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def insert_provenance(self, record: dict[str, Any]) -> None:
        cols = [
            "record_id",
            "dataset_id",
            "source_url",
            "retrieved_at",
            "valid_time",
            "init_time",
            "lead_time",
            "calculation_method",
            "parameters",
            "baseline_period",
            "geographic_aggregation",
            "missing_data_handling",
            "output_timestamp",
            "code_version",
            "notes",
        ]
        values = {c: record.get(c) for c in cols}
        values["parameters"] = (
            json.dumps(values["parameters"], default=str) if values["parameters"] else None
        )
        placeholders = ", ".join("?" for _ in cols)
        self.execute(
            f"INSERT INTO provenance ({', '.join(cols)}) VALUES ({placeholders})",
            tuple(values[c] for c in cols),
        )

    def record_ingestion(
        self,
        source_id: str,
        status: str,
        message: str = "",
        retrieved_at: str | None = None,
        valid_time: str | None = None,
    ) -> None:
        self.execute(
            "INSERT INTO ingestion_history (source_id, status, message, retrieved_at, valid_time) "
            "VALUES (?, ?, ?, ?, ?)",
            (source_id, status, message, retrieved_at, valid_time),
        )

    def close(self) -> None:
        self._conn.close()
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
