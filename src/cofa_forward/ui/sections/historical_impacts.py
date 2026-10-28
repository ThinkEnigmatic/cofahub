"""Historical Impacts — structured impact catalog."""

from __future__ import annotations

import streamlit as st

from ...impacts.event_catalog import load_catalog
from ...impacts.impact_analysis import summarize_by_country
from ..components.common import page_header, sample_banner
from ..state import get_sample_impacts


def render() -> None:
    page_header("Historical Impacts", "Documented droughts, rainfall extremes, and cyclone impacts")

    sample_banner()
    df = get_sample_impacts()
    catalog = load_catalog(df)

    st.caption(
        "The catalog distinguishes **documented** impacts from **inferred** and **modeled** "
        "estimates, and never implies a report covers a whole country when it only describes "
        "one island. Current entries are synthetic and clearly labeled."
    )

    st.subheader("Impact events")
    st.dataframe(catalog.all(), width="stretch", hide_index=True)

    st.divider()

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Events by country & hazard")
        st.dataframe(summarize_by_country(catalog), width="stretch", hide_index=True)
    with right:
        st.subheader("Evidence & confidence")
        st.write(
            "Every record carries `evidence_quality` and `confidence` fields. "
            "Synthetic records are labeled `sample`; real records will use "
            "`documented` / `inferred` / `modeled`."
        )

    st.divider()
    st.info(
        "Authoritative impact reports (and full-text indexing for RAG) arrive in Phase 6. "
        "Until then, no impact counts are fabricated.",
        icon="📚",
    )
