"""Shared Streamlit UI components and helpers."""

from __future__ import annotations

import streamlit as st

from ...timeutil import now_utc


def page_header(title: str, subtitle: str = "") -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def sample_banner() -> None:
    """Unambiguous, always-visible label that the data shown is synthetic sample data."""
    st.warning(
        "**SAMPLE DATA** — the figures on this page are synthetic, clearly labeled "
        "demonstration data, not live observations or forecasts. Live data is shown only "
        "when a real provider is fetched and its provenance is displayed.",
        icon="⚠️",
    )


def live_badge(from_cache: bool = False) -> None:
    label = "LIVE (cached)" if from_cache else "LIVE"
    st.success(label, icon="✅")


def stale_badge(timestamp: str | None, max_age_hours: float = 24.0) -> bool:
    """Show a stale indicator if a timestamp is older than the threshold. Returns stale bool."""
    if not timestamp:
        st.info("No timestamp available", icon="ℹ️")
        return True
    from ...timeutil import normalize_timestamp

    ts = normalize_timestamp(timestamp)
    age_h = (now_utc() - ts).total_seconds() / 3600.0
    if age_h > max_age_hours:
        st.warning(
            f"Stale — last data {ts.strftime('%Y-%m-%d %H:%M UTC')} ({age_h:.0f} h ago)", icon="🕓"
        )
        return True
    st.caption(f"Data timestamp: {ts.strftime('%Y-%m-%d %H:%M UTC')}")
    return False


def metric(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label=label, value=value, help=help_text)


def evidence_badge(evidence_type: str) -> str:
    """Map an evidence type to an emoji tag for inline display."""
    return {
        "observed": "🔵 observed",
        "forecast": "🟡 forecast",
        "official": "🟢 official",
        "historical": "🟣 historical",
        "modeled": "🟠 modeled",
        "analyst": "⚪ analyst interpretation",
    }.get(evidence_type, "⚪ " + str(evidence_type))


def source_caption(
    units: str = "",
    valid_time: str = "",
    init_time: str = "",
    source: str = "",
    resolution: str = "",
) -> None:
    parts = [
        p
        for p in (
            f"Units: {units}" if units else "",
            f"Valid: {valid_time}" if valid_time else "",
            f"Init: {init_time}" if init_time else "",
            f"Source: {source}" if source else "",
            f"Resolution: {resolution}" if resolution else "",
        )
        if p
    ]
    if parts:
        st.caption(" · ".join(parts))


def render_plotly(fig, key: str | None = None, use_container_width: bool = True) -> None:
    width = "stretch" if use_container_width else "content"
    st.plotly_chart(fig, width=width, key=key)


def empty_state(message: str) -> None:
    st.info(message, icon="ℹ️")
