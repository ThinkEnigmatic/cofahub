"""Reports — reproducible daily intelligence brief."""

from __future__ import annotations

import streamlit as st

from ...intelligence.report_builder import build_markdown_report
from ...intelligence.synthesis import build_statements
from ...timeutil import format_iso, now_utc
from ..components.common import page_header, sample_banner
from ..state import get_all_indicators, load_config


def assemble_brief() -> str:
    cfg = load_config()
    indicators = get_all_indicators()
    stmts = build_statements(indicators, cfg.enso_current)

    flagged = [i for i in indicators if i.get("percentile") is not None and i["percentile"] < 0.2]
    flagged_names = (
        ", ".join(i["name"] for i in sorted(flagged, key=lambda x: x["percentile"])) or "none"
    )

    meta = {
        "report_date": format_iso(now_utc())[:10],
        "data_cutoff": format_iso(now_utc()),
        "region": cfg.app.get("region", "Freely Associated States"),
        "mode": "sample data (no live providers fetched)",
    }

    sections = [
        {
            "title": "Regional situation summary",
            "items": stmts,
        },
        {
            "title": "Weather & rainfall outlook",
            "items": [
                {
                    "text": "Short-range forecast is available on the Weather Operations page "
                    "(sample by default; live via Open-Meteo on demand).",
                    "evidence_type": "analyst",
                    "source": "Open-Meteo (live) / synthetic sample",
                }
            ],
        },
        {
            "title": "Drought & freshwater concerns",
            "items": [
                {
                    "text": f"Locations below the 20th-percentile watch level: {flagged_names}.",
                    "evidence_type": "observed",
                    "source": "computed percentile indicator (sample series)",
                },
                {
                    "text": "Freshwater shortage is not inferred from rainfall deficit alone; "
                    "non-meteorological inputs are listed as missing.",
                    "evidence_type": "analyst",
                },
            ],
        },
        {
            "title": "Tropical cyclone situation",
            "items": [
                {
                    "text": "No confirmed active storms in available data; no official track "
                    "source is wired in, and none are fabricated.",
                    "evidence_type": "analyst",
                }
            ],
        },
        {
            "title": "Historical analogs",
            "items": [
                {
                    "text": "Analogs are selected by explainable numeric similarity once a "
                    "historical dataset is available (Phase 3). No analog is asserted now.",
                    "evidence_type": "analyst",
                }
            ],
        },
    ]

    sources = [
        {"source_id": s.id, "retrieved_at": "—", "status": s.implementation_status}
        for s in cfg.sources()
    ]

    gaps = [
        "No authoritative ENSO source is configured; current phase is not assumed.",
        "No official seasonal outlook is integrated.",
        "No live weather/rainfall fetch has been performed in this session.",
        "Percentile indicators are computed over a synthetic sample series, not real data.",
        "Individual-atoll interpretation of coarse model grids is not atoll-accurate.",
    ]

    return build_markdown_report(meta, sections, sources, gaps)


def render() -> None:
    page_header("Reports", "Reproducible, evidence-linked daily brief")

    sample_banner()
    st.caption(
        "The brief uses the same analytical outputs as the dashboard. Forecasts are "
        "distinguished from observations, official outlooks, historical analogs, and "
        "analyst interpretation."
    )

    brief = assemble_brief()

    st.download_button(
        "Download Markdown brief",
        data=brief,
        file_name=f"cofa-forward-brief-{format_iso(now_utc())[:10]}.md",
        mime="text/markdown",
    )

    st.markdown(brief)
