"""AI Analysis — chat with the LLM, grounded in the app's real dataset."""

from __future__ import annotations

import streamlit as st

from ...cyclones.proximity import closest_approach
from ...drought.el_nino_comparison import build_comparison
from ...drought.percentiles import drought_level, empirical_percentile
from ...impacts.event_catalog import load_catalog
from ...intelligence.analysis_context import build_location_snapshot
from ...intelligence.llm_client import LLMClient
from ..components.common import page_header
from ..state import (
    get_active_storms,
    get_el_nino_comparison_rainfall,
    get_enso_discussion,
    get_jtwc_warnings,
    get_live_enso,
    get_model_comparison,
    get_nmme_multimodel,
    get_nws_guam_advisory,
    get_sample_impacts,
    get_sample_tracks,
    get_worldpop_population,
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

    # ---- ENSO ----
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

    # ---- Rainfall (ERA5) + percentile + drought level + El Niño history ----
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

    # ---- Active cyclones (JMA + JTWC) ----
    active = get_active_storms()
    jtwc = get_jtwc_warnings()
    storms = []
    if active.get("ok") and active.get("n_active"):
        for s in active["storms"]:
            storms.append(
                {
                    "name": s.get("name") or s.get("tc_id"),
                    "storm_id": s.get("tc_id"),
                    "wind_kt": None,
                }
            )
    if jtwc.get("ok") and jtwc.get("n_active"):
        for w in jtwc["storms"]:
            storms.append(
                {
                    "name": w.get("name"),
                    "storm_id": w.get("storm_id"),
                    "wind_kt": w.get("wind_kt"),
                    "position": w.get("position"),
                }
            )
    if storms or active.get("ok") or jtwc.get("ok"):
        facts["cyclones_active"] = {
            "n_active": len(storms) or active.get("n_active", 0),
            "source": "JMA RSMC Tokyo + JTWC",
            "storms": storms,
        }

    # ---- NWS Guam watches/warnings ----
    nwsg = get_nws_guam_advisory()
    if nwsg.get("ok"):
        facts["cyclones_watch"] = {
            "headline": nwsg.get("headline"),
            "watches_warnings": nwsg.get("watches_warnings", []),
        }

    # ---- Historical cyclone proximity (sample tracks, labeled) ----
    tracks = get_sample_tracks()
    if tracks is not None and not tracks.empty:
        ca = closest_approach(entity.latitude, entity.longitude, tracks)
        facts["cyclones_history"] = {
            "n_storms": int(tracks["storm_id"].nunique()),
            "closest_km": ca.get("distance_km") if ca else None,
            "closest_time": str(ca.get("time")) if ca else None,
            "note": "sample tracks (illustrative)",
        }

    # ---- Forecasts (NMME seasonal + Open-Meteo multi-model) ----
    forecast = {}
    nmme = get_nmme_multimodel(entity.latitude, entity.longitude, variable="prate")
    if nmme.get("ok"):
        mean = nmme.get("ensemble_mean")
        spread = nmme.get("ensemble_std")
        forecast["nmme_cycle"] = nmme.get("cycle")
        forecast["nmme_models"] = nmme.get("n_models")
        if mean is not None and len(mean):
            forecast["nmme_mean_mm"] = float(mean.iloc[0])
            forecast["nmme_spread_mm"] = (
                float(spread.iloc[0]) if spread is not None and len(spread) else None
            )
    mc = get_model_comparison(entity.latitude, entity.longitude, variable="temperature_2m")
    if mc.get("ok"):
        forecast["short_models"] = mc.get("n_models")
    if forecast:
        facts["forecast"] = forecast

    # ---- Historical impacts (sample catalog, labeled) ----
    try:
        cat = load_catalog(get_sample_impacts())
        df = cat.by_geo_id(entity.geo_id)
        if df.empty and entity.parent_geo_id:
            df = cat.by_geo_id(entity.parent_geo_id)
        if not df.empty:
            facts["impacts"] = {
                "n_events": int(len(df)),
                "note": "sample catalog (illustrative)",
                "events": [
                    {
                        "event_name": r.get("event_name"),
                        "hazard_type": r.get("hazard_type"),
                        "start_date": r.get("start_date"),
                        "reported_impacts": r.get("reported_impacts"),
                    }
                    for _, r in df.iterrows()
                ],
            }
    except Exception:  # noqa: BLE001 - defensive; impacts are optional context
        pass

    # ---- Water (freshwater framework) ----
    cfg = load_config()
    fw = cfg.freshwater
    facts["water"] = {
        "note": "Freshwater risk is not equated with a rainfall anomaly.",
        "available_inputs": fw.get("available_inputs", []),
        "missing_inputs": fw.get("missing_inputs", []),
    }

    # ---- Population exposure ----
    pop = get_worldpop_population(geo_id, entity.country_code, entity.latitude, entity.longitude)
    if pop.get("ok"):
        facts["population"] = {
            "population": pop.get("population"),
            "radius_km": pop.get("radius_km"),
        }

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
        "Sandboxed: the model is a read-only text pipe with no tools, no code "
        "execution, and no access beyond the snapshot above. It is told not to "
        "invent numbers. Treat its output as advisory, not an official forecast."
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
            "“Is this location in drought right now?”, "
            "“What cyclones have approached this atoll?”, or "
            "“Summarize the El Niño drought history for this location.”",
            icon="💬",
        )
