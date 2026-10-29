"""Data Sources & System Health."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ... import __version__
from ..components.common import page_header
from ..state import get_snapshot_status, load_config, make_db

_STATUS_ICON = {
    "implemented_and_tested": "✅",
    "implemented_but_not_verified": "🟡",
    "requires_credentials": "🔑",
    "requires_manual_import": "📥",
    "planned": "🗓️",
    "unavailable": "🚫",
}

_STATE_FILE = Path(__file__).resolve().parents[4] / "data" / "weathernext_status.json"


def _weathernext_status() -> dict:
    """Read the WeatherNext approval monitor's state file (best-effort)."""
    try:
        if _STATE_FILE.is_file():
            import json

            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        pass
    return {}


def render() -> None:
    cfg = load_config()
    page_header("Data Sources & System Health", "Provider status, ingestion history, provenance")

    try:
        db = make_db()
    except Exception as exc:  # pragma: no cover - defensive
        db = None
        st.warning(f"Could not open metadata DB: {exc}")

    st.subheader("Application")
    st.write(f"- Version: **{__version__}**")
    st.write(f"- Geographic registry status: **{cfg.geography_status}** (seed, approximate)")
    st.write(f"- Default units: **{cfg.default_units}** (imperial optional)")

    st.divider()

    # ---- Offline snapshot status ---- #
    snap = get_snapshot_status()
    if snap["offline"]:
        st.subheader("📴 Offline mode (snapshot)")
        st.write(
            f"Snapshot captured **{snap['snapshot_at']}** — "
            f"**{snap['ok_sources']}/{snap['n_sources']}** sources available."
        )
        if snap["missing"]:
            st.warning(f"Missing from snapshot: {', '.join(snap['missing'])}", icon="⚠️")
        st.caption(
            "Set COFA_OFFLINE=1 to serve the pre-fetched snapshot; unset it to fetch live "
            "data. Refresh the snapshot with `scripts/prefetch_snapshot.py` (or the macOS app's "
            '"Refresh snapshot" button).'
        )
    else:
        st.subheader("📡 Online mode")
        if snap["snapshot_at"]:
            st.write(
                f"A snapshot from **{snap['snapshot_at']}** is present on disk "
                f"({snap['ok_sources']}/{snap['n_sources']} sources) for offline fallback."
            )
        else:
            st.write("No offline snapshot has been captured yet.")

    st.divider()

    # ---- WeatherNext access request status (read from the monitor's state file) ---- #
    _wn = _weathernext_status()
    if _wn:
        icon = {"pending": "🕓", "approved": "✅", "rejected": "🚫"}.get(_wn.get("status"), "❓")
        st.subheader(f"{icon} WeatherNext 3 access request")
        st.write(
            f"Status: **{_wn.get('status', 'unknown').upper()}** (checked {_wn.get('checked_at')})"
        )
        st.write(
            f"Account: `{_wn.get('account')}` · Form submitted {_wn.get('form_submitted')} · "
            f"approval {_wn.get('approval_window')}."
        )
        if _wn.get("latest_message"):
            lm = _wn["latest_message"]
            st.write(f"Latest message: **{lm.get('from')}** — {lm.get('subject')}")
        st.caption(
            "Monitored by launchd (com.ben.cofaforward-weathernext-monitor, hourly). "
            "Once approved, read Zarr via gcsfs with GOOGLE_APPLICATION_CREDENTIALS or "
            "`gcloud auth application-default login` for hemingwayglobal77@gmail.com."
        )

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
    history = []
    if db is not None:
        history = db.query(
            "SELECT source_id, status, message, retrieved_at FROM ingestion_history "
            "ORDER BY id DESC LIMIT 25"
        )

    if history:
        st.dataframe(pd.DataFrame(history), width="stretch", hide_index=True)
    else:
        st.info("No ingestion has been recorded yet (no live fetches performed).", icon="ℹ️")

    st.divider()

    st.subheader("Bulletins & alerts (monitor)")
    st.write(
        "Polls public bulletins (NWS Guam, JTWC, JMA, CPC ENSO) for new or updated "
        "content, parses a summary, stores a raw snapshot, and logs each update."
    )
    if st.button("Run bulletin monitor now"):
        from ...ingestion.bulletins import BulletinMonitor
        from ...storage.cache import FileCache

        with st.spinner("Polling bulletin sources…"):
            monitor = BulletinMonitor(
                cfg, cache=FileCache(cfg.data_dir("cache"), cfg.cache_ttl_seconds), db=db
            )
            updates = monitor.check_all()
        if updates:
            for u in updates:
                st.success(
                    f"Updated: {u['name']} ({u['retrieved_at']}) — {u['summary']}", icon="📣"
                )
        else:
            st.info("No new or updated bulletins detected.", icon="✅")

    recent = db.recent_bulletins(20) if db is not None else []
    if recent:
        st.dataframe(
            pd.DataFrame(recent)[["source_id", "name", "retrieved_at", "summary"]],
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption("No bulletin updates recorded yet — run the monitor (or schedule it).")

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
