"""Build a grounded data snapshot for LLM analysis.

The snapshot is a deterministic, labelled text block assembled from the SAME
computed indicators and live data the dashboard uses. It exists so that when a
user asks the LLM a question, the model answers from real values (with provenance)
rather than from its own prior — and it makes it obvious to the user exactly what
the model was allowed to see.
"""

from __future__ import annotations

from typing import Any


def _num(x: Any, fmt: str = "{:.1f}") -> str:
    if x is None:
        return "n/a"
    try:
        return fmt.format(float(x))
    except (TypeError, ValueError):
        return str(x)


def build_location_snapshot(facts: dict[str, Any]) -> str:
    """Render a compact text snapshot from a dict of pre-assembled facts.

    ``facts`` may carry: ``location`` (name/geo_id/type/lat/lon/population),
    ``enso`` (phase/anom/season/alert), ``rainfall`` (latest month mm, anomaly %,
    percentile, drought level, baseline), ``el_nino`` (per-event rolling6 minima +
    current), ``cyclones`` (n storms / closest approach), ``water`` (framework note).
    Missing keys render as "not provided" and are never fabricated.
    """
    lines: list[str] = []

    loc = facts.get("location") or {}
    if loc:
        lines.append(
            "LOCATION: "
            + f"{loc.get('name', '?')} ({loc.get('geo_id', '?')}) · "
            + f"type={loc.get('type', '?')} · {_num(loc.get('lat'), '{:.2f}')}°N, "
            + f"{_num(loc.get('lon'), '{:.2f}')}°E"
            + (
                f" · population≈{_num(loc.get('population'), '{:.0f}')}"
                if loc.get("population")
                else ""
            )
        )

    enso = facts.get("enso") or {}
    if enso:
        lines.append(
            "ENSO: "
            + f"phase={enso.get('phase', 'n/a')} · ONI {enso.get('season', '?')} "
            + f"{enso.get('year', '?')} = {_num(enso.get('anom'), '{:+.2f}')}°C"
            + (f" · alert={enso.get('alert', 'n/a')}" if enso.get("alert") else "")
        )

    rain = facts.get("rainfall") or {}
    if rain:
        lines.append(
            "RAINFALL (latest month): "
            + f"total={_num(rain.get('latest_mm'), '{:.0f}')} mm · "
            + f"anomaly={_num(rain.get('anomaly_pct'), '{:+.0f}')}% · "
            + f"percentile={_num(rain.get('percentile'), '{:.0%}')} · "
            + f"drought level={rain.get('drought_level', 'n/a')}"
            + (f" · baseline={rain.get('baseline', '?')}" if rain.get("baseline") else "")
            + (f" · source={rain.get('source', '?')}" if rain.get("source") else "")
        )

    elnino = facts.get("el_nino") or {}
    if elnino:
        for ev_id in ("2015-16", "1997-98", "2023-24"):
            if ev_id in elnino:
                e = elnino[ev_id]
                lines.append(
                    f"EL NIÑO {ev_id}: rolling 6-mo rainfall minimum "
                    f"{_num(e.get('min_pct'), '{:.0f}')}% of normal "
                    f"(at aligned month {_num(e.get('min_month'), '{:.0f}')})"
                )
        cur = elnino.get("current")
        if cur:
            lines.append(
                "CURRENT CYCLE: latest rolling 6-mo rainfall "
                f"{_num(cur.get('rolling6_pct'), '{:.0f}')}% of normal"
            )

    cyc = facts.get("cyclones") or {}
    if cyc:
        lines.append(
            "CYCLONES: "
            + f"{_num(cyc.get('n_storms'), '{:.0f}')} historical storms · "
            + f"closest approach {_num(cyc.get('closest_km'), '{:.0f}')} km"
        )

    water = facts.get("water") or {}
    if water:
        lines.append(f"WATER: {water.get('note', '')}")

    if not lines:
        return "No data available for this location."

    lines.append(
        "NOTE: values are real computed/live data; n/a means missing. Baseline is 1991–2020."
    )
    return "\n".join(lines)
