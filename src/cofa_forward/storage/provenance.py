"""Provenance recording.

Every derived value must be traceable. ``ProvenanceStore`` persists structured
provenance records to the SQLite metadata store.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import __version__
from ..timeutil import now_utc
from .database import Database


class ProvenanceStore:
    """Records provenance for ingested and derived data."""

    def __init__(self, db: Database):
        self.db = db

    def record(self, **fields: Any) -> None:
        record = {
            "output_timestamp": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "code_version": __version__,
        }
        record.update(fields)
        self.db.insert_provenance(record)


def build_provenance(
    dataset_id: str | None = None,
    source_url: str | None = None,
    retrieved_at: str | None = None,
    valid_time: str | None = None,
    init_time: str | None = None,
    lead_time: str | None = None,
    calculation_method: str | None = None,
    parameters: dict[str, Any] | None = None,
    baseline_period: str | None = None,
    geographic_aggregation: str | None = None,
    missing_data_handling: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Construct a provenance record dict (for storage or inline reporting)."""
    return {
        "dataset_id": dataset_id,
        "source_url": source_url,
        "retrieved_at": retrieved_at,
        "valid_time": valid_time,
        "init_time": init_time,
        "lead_time": lead_time,
        "calculation_method": calculation_method,
        "parameters": parameters,
        "baseline_period": baseline_period,
        "geographic_aggregation": geographic_aggregation,
        "missing_data_handling": missing_data_handling,
        "notes": notes,
    }


def default_db_path(root: Path | str) -> Path:
    return Path(root) / "data" / "catalog.db"
