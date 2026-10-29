"""National Plans & Guidance — government drought plans and emergency declarations."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ...guidance.national_plans import NATIONAL_PLANS
from ..components.common import evidence_badge, page_header


def render() -> None:
    page_header(
        "National Plans & Guidance",
        "Government drought plans, emergency declarations, and response frameworks",
    )

    st.caption(
        "These are the authoritative national documents that turn the app's scientific "
        "drought classification (quintile Rainfall Index, PEAC 4/8-inch Index, D0–D4) into "
        "concrete government triggers and response actions."
    )

    st.divider()

    # ---- Analytical linkages (the point of pulling these in) ---- #
    st.subheader("What the plans tell the analysis")
    st.markdown(
        "- **RMI** zones atolls by latitude: **Zone 1 (>8°N) and Zone 2 (6°–8°N) are the "
        "government-designated *high-vulnerability* drought areas** — the northern atolls. "
        "This matches the app's independent finding that northern RMI atolls are the most "
        "drought-exposed (see the El Niño Comparison page).\n"
        "- **Palau** uses a *stage-based* trigger (Stage 1 = water-shortage watch), activated "
        "by the National Emergency Committee on National Weather Service monitoring.\n"
        "- **FSM** uses a *three-pillar* framework (early warning, vulnerability/impact "
        "assessment, mitigation–preparedness–response), endorsed Aug 2026."
    )

    st.divider()

    # ---- Document catalog ---- #
    st.subheader("Documents")
    rows = [
        {
            "Country": p["country"],
            "Type": p["doc_type"].replace("_", " "),
            "Title": p["title"],
            "Date": p["date"] or "—",
            "Publisher": p["publisher"],
            "Status": "✅ verified"
            if p["verification_status"] == "verified"
            else p["verification_status"],
            "Source": p["url"],
        }
        for p in NATIONAL_PLANS
    ]
    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
        hide_index=True,
        column_config={"Source": st.column_config.LinkColumn("Source")},
    )

    st.divider()

    # ---- Per-country detail ---- #
    for p in NATIONAL_PLANS:
        with st.expander(f"{p['country']} — {p['title']} ({p['date'] or 'n.d.'})"):
            st.markdown(p["summary"])
            st.markdown("**Key facts (extracted from the cited document):**")
            for f in p["key_facts"]:
                st.markdown(f"- {f}")
            st.markdown(
                f"{evidence_badge('official')} Source: [{p['url']}]({p['url']}) — "
                f"extracted {p['extraction_date']} via {p['extraction_method']}."
            )

    st.divider()
    st.caption(
        "These documents are guidance and historical record, not live triggers. The app does "
        "not assert a current government drought status — it presents the national frameworks "
        "alongside the live scientific indicators so a planner can see where conditions stand "
        "relative to each country's own triggers."
    )
