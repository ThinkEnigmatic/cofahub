"""AI Analysis — chat with the LLM, grounded in the app's real dataset."""

from __future__ import annotations

import streamlit as st

from ...drought.el_nino_comparison import build_comparison
from ...drought.percentiles import drought_level, empirical_percentile
from ...intelligence.analysis_context import build_location_snapshot
from ...intelligence.llm_client import LLMClient
from ..components.common import page_header
from ..state import (
    get_el_nino_comparison_rainfall,
    get_enso_discussion,
    get_live_enso,
    load_config,
    load_registry,
)


def _assemble_facts(geo_id: str, entity) -> dict:
    """Gather the real data snapshot for a location (best-effort, never raises)."""
    facts: dict = {}
    facts["location"] = {
        "name": entity.name,
        "geo_id": entity.geo_id,
        "type": entity.entity_type,
        "lat": entity.latitude,
        "lon": entity.longitude,
        "population": entity.population,
    }

    # ENSO
    enso = get_live_enso()
    if enso.get("ok"):
        latest = enso["latest"]
        facts["enso"] = {
            "phase": enso.get("phase"),
            "season": latest.get("season"),
            "year": latest.get("year"),
            "anom": latest.get("anom"),
        }
    disc = get_enso_discussion()
    if disc.get("ok") and facts.get("enso"):
        facts["enso"]["alert"] = disc.get("alert_status")

    # Rainfall (ERA5) + percentile + drought level
    rain = get_el_nino_comparison_rainfall(geo_id, entity.latitude, entity.longitude)
    if rain.get("ok"):
        daily = rain["series"]
        comparison = build_comparison(daily)
        monthly = comparison["monthly"]
        clim = comparison["climatology"]
        if not monthly.empty and not clim.empty:
            lm = monthly.iloc[-1]
            lm_clim = clim.get(monthly.index[-1].month)
            anomaly_pct = (float(lm) / float(lm_clim) - 1.0) * 100.0 if lm_clim else None
            pct = empirical_percentile(float(lm), monthly)
            facts["rainfall"] = {
                "latest_mm": float(lm),
                "anomaly_pct": anomaly_pct,
                "percentile": pct,
                "drought_level": drought_level(pct),
                "baseline": comparison.get("baseline"),
                "source": "ERA5 (Open-Meteo archive)",
            }

        # El Niño comparison minima
        elnino = {}
        for ev_id in ("2015-16", "1997-98", "2023-24"):
            e = comparison["events"][ev_id]
            y = e["rolling6_pct_aligned"]
            if y.notna().any():
                elnino[ev_id] = {
                    "min_pct": float(y.min()),
                    "min_month": int(y.argmin()),
                }
        cur = comparison["current"]["rolling6_pct"]
        if cur.notna().any():
            elnino["current"] = {"rolling6_pct": float(cur.iloc[-1])}
        facts["el_nino"] = elnino

    facts["water"] = {"note": "Freshwater risk is not equated with a rainfall anomaly."}
    return facts


def render() -> None:
    cfg = load_config()
    registry = load_registry()
    page_header("AI Analysis", "Chat with a model grounded in the app's real data")

    client = LLMClient(config=cfg)
    if not client.available:
        st.warning(
            "No LLM endpoint is configured. Set `COFA_LLM_API_KEY` (or run the local "
            "model gateway so its token file is present) to enable chat analysis.",
            icon="🔑",
        )

    names = {e.geo_id: e.name for e in registry.all()}
    geo_id = st.selectbox(
        "Location for analysis",
        options=list(names.keys()),
        format_func=lambda g: f"{names[g]} ({g})",
    )
    entity = registry.by_id(geo_id)

    with st.spinner("Loading live data for this location…"):
        facts = _assemble_facts(geo_id, entity)
    snapshot = build_location_snapshot(facts)

    with st.expander("Data snapshot the model can see"):
        st.code(snapshot, language="text")

    st.caption(
        "The model answers from the snapshot above only — it is told not to invent "
        "numbers. Treat its output as advisory, not as an official forecast."
    )

    # Chat state
    if "ai_chat" not in st.session_state:
        st.session_state["ai_chat"] = []

    for turn in st.session_state["ai_chat"]:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])

    question = st.chat_input("Ask about this location's data…")
    if question:
        st.session_state["ai_chat"].append({"role": "user", "content": question})
        if not client.available:
            st.session_state["ai_chat"].append(
                {"role": "assistant", "content": "⚠️ LLM is not configured."}
            )
            st.rerun()
        with st.spinner("Analyzing…"):
            result = client.analyze(snapshot, question)
        answer = result["text"] if result.get("ok") else f"⚠️ LLM call failed: {result.get('error')}"
        st.session_state["ai_chat"].append({"role": "assistant", "content": answer})
        st.rerun()

    if not st.session_state["ai_chat"]:
        st.info(
            "Try: “How does the current cycle compare to 2015-16 here?”, "
            "“Is this location in drought right now?”, or "
            "“Summarize the El Niño drought history for this atoll.”",
            icon="💬",
        )
