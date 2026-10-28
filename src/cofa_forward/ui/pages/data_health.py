"""Data Sources & System Health."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ... import __version__
from ..components.common import page_header
from ..state import load_config, make_db

_STATUS_ICON = {
    "implemented_and_tested": "✅",
    "implemented_but_not_verified": "🟡",
    "requires_credentials": "🔑",
    "requires_manual_import": "📥",
    "planned": "🗓️",
    "unavailable": "🚫",
}


def render() -> None:
    cfg = load_config()
    page_header("Data Sources & System Health", "Provider status, ingestion history, provenance")

    st.subheader("Application")
    st.write(f"- Version: **{__version__}**")
    st.write(f"- Geographic registry status: **{cfg.geography_status}** (seed, approximate)")
    st.write(f"- Default units: **{cfg.default_units}** (imperial optional)")

    st.divider()

    st.subheader("Data source catalog")
    sources = cfg.sources()
    rows = [
        {
            "Status": _STATUS_ICON.get(s.implementation_status, "") + " " + s.implementation_status,
            "Source": s.name,
            "Publisher": s.publisher,
            "License": s.license or "—",
            "Coverage": s.geographic_coverage or "—",
            "Resolution": s.spatial_resolution or "—",
            "Auth": s.auth or "none",
            "Verified": s.verification_date or "—",
        }
        for s in sources
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption(
        "Status legend: ✅ implemented & tested · 🟡 implemented, not verified · 🔑 requires "
        "credentials · 📥 requires manual import · 🗓️ planned · 🚫 unavailable. A source is "
        "marked ✅ only after a successful integration test."
    )

    st.divider()

    st.subheader("Ingestion history")
    try:
        db = make_db()
        history = db.query(
            "SELECT source_id, status, message, retrieved_at FROM ingestion_history "
            "ORDER BY id DESC LIMIT 25"
        )
    except Exception as exc:  # pragma: no cover - defensive
        history = []
        st.warning(f"Could not read ingestion history: {exc}")

    if history:
        st.dataframe(pd.DataFrame(history), width="stretch", hide_index=True)
    else:
        st.info("No ingestion has been recorded yet (no live fetches performed).", icon="ℹ️")

    st.divider()

    st.subheader("Provenance & scientific integrity")
    st.write(
        "Every derived value records its input datasets, source timestamps, calculation "
        "method, parameters, baseline period, geographic aggregation, missing-data "
        "handling, and code version. Uncertainty is shown where available; no numerical "
        "confidence values are manufactured."
    )
    st.caption(
        "Retrieved documents and any future LLM output are treated as untrusted data and "
        "can never override system behavior or execute instructions."
    )
