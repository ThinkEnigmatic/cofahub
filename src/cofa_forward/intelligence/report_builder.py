"""Reproducible Markdown daily intelligence brief.

Uses the SAME analytical outputs as the dashboard. Deterministic (no LLM).
Distinguishes observed / forecast / official / historical / modeled / analyst
statements and always lists sources, timestamps, and known gaps.
"""

from __future__ import annotations

from typing import Any

_EVIDENCE_TAG = {
    "observed": "observed",
    "forecast": "forecast",
    "official": "official",
    "historical": "historical",
    "modeled": "modeled",
    "analyst": "analyst interpretation",
}


def _line(item: dict[str, Any]) -> str:
    tag = _EVIDENCE_TAG.get(item.get("evidence_type"), "analyst interpretation")
    text = item.get("text", "")
    source = item.get("source")
    suffix = f"  _(source: {source})_" if source else ""
    return f"- [{tag}] {text}{suffix}"


def build_markdown_report(
    meta: dict[str, Any],
    sections: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    gaps: list[str] | None = None,
) -> str:
    """Assemble a dated Markdown brief from structured sections.

    Parameters
    ----------
    meta:
        ``report_date``, ``data_cutoff``, ``region`` (and any extra fields).
    sections:
        List of ``{"title": str, "items": [{"text", "evidence_type", "source"}]}``.
    sources:
        List of ``{"source_id", "retrieved_at", "status"}`` for the data log.
    gaps:
        List of information-gap / uncertainty strings.
    """
    lines: list[str] = []
    lines.append("# COFA FORWARD — Daily Intelligence Brief")
    lines.append("")
    lines.append(f"- **Report date:** {meta.get('report_date', 'n/a')}")
    lines.append(f"- **Data cutoff:** {meta.get('data_cutoff', 'n/a')}")
    lines.append(f"- **Region:** {meta.get('region', 'Freely Associated States')}")
    for k, v in meta.items():
        if k not in ("report_date", "data_cutoff", "region"):
            lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append(
        "> Evidence tags distinguish the nature of each statement. "
        "Forecasts are not observations; historical analogs are not forecasts; "
        "analyst interpretation is judgment, not measurement."
    )
    lines.append("")

    for section in sections:
        lines.append(f"## {section['title']}")
        lines.append("")
        for item in section.get("items", []):
            lines.append(_line(item))
        lines.append("")

    lines.append("## Information gaps & uncertainty")
    lines.append("")
    if gaps:
        for g in gaps:
            lines.append(f"- {g}")
    else:
        lines.append("- None recorded.")
    lines.append("")

    lines.append("## Data sources & timestamps")
    lines.append("")
    lines.append("| Source | Retrieved | Status |")
    lines.append("| --- | --- | --- |")
    for s in sources:
        lines.append(
            f"| {s.get('source_id', '')} | {s.get('retrieved_at', '')} | {s.get('status', '')} |"
        )
    lines.append("")

    return "\n".join(lines)
