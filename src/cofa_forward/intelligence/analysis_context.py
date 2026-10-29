"""Build a grounded data snapshot for LLM analysis.

The snapshot is a deterministic, labelled text block assembled from the SAME
computed indicators and live data the dashboard uses. It exists so that when a
user asks the LLM a question, the model answers from real values (with provenance)
rather than from its own prior — and it makes it obvious to the user exactly what
the model was allowed to see.

All event types are represented (cyclones, forecasts, impacts, drought, ENSO, El
Niño history, water). Missing data renders as "n/a" / "not provided" and is never
fabricated. The snapshot contains no secrets, paths, or configuration.
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

    Supported top-level keys (all optional): ``location``, ``enso``, ``rainfall``,
    ``el_nino``, ``cyclones_active``, ``cyclones_history``, ``forecast``,
    ``impacts``, ``water``, ``population``. Missing keys render as "not provided".
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

    active = facts.get("cyclones_active") or {}
    if active:
        n = active.get("n_active", 0)
        if n:
            lines.append(f"ACTIVE CYCLONES: {n} (source {active.get('source', 'n/a')})")
            for s in active.get("storms", []):
                pos = s.get("position") or {}
                bits = [
                    f"  - {s.get('name', '?')} ({s.get('storm_id', s.get('tc_id', '?'))})",
                    f"wind {_num(s.get('wind_kt'), '{:.0f}')} kt",
                ]
                if pos:
                    bits.append(
                        f"at {_num(pos.get('lat'), '{:.1f}')}°N {_num(pos.get('lon'), '{:.1f}')}°E"
                    )
                lines.append(" ".join(bits))
        else:
            lines.append(f"ACTIVE CYCLONES: none (source {active.get('source', 'n/a')})")

    watch = facts.get("cyclones_watch") or {}
    if watch:
        if watch.get("headline"):
            lines.append(f"WATCH/WARNING: {watch['headline']}")
        for w in watch.get("watches_warnings", [])[:6]:
            lines.append(f"  - {w}")

    hist = facts.get("cyclones_history") or {}
    if hist:
        lines.append(
            "CYCLONE HISTORY: "
            + f"{_num(hist.get('n_storms'), '{:.0f}')} storms · "
            + f"closest approach {_num(hist.get('closest_km'), '{:.0f}')} km "
            + f"({hist.get('closest_time', 'n/a')})"
        )

    fc = facts.get("forecast") or {}
    if fc:
        lines.append(
            "SEASONAL FORECAST: "
            + f"NMME {fc.get('nmme_cycle', 'n/a')} · "
            + f"{_num(fc.get('nmme_models'), '{:.0f}')} models · "
            + f"ensemble-mean precip {_num(fc.get('nmme_mean_mm'), '{:.2f}')} mm/day "
            + f"(spread {_num(fc.get('nmme_spread_mm'), '{:.2f}')})"
        )
        lines.append(
            "SHORT-RANGE FORECAST: "
            + f"{_num(fc.get('short_models'), '{:.0f}')} models (Open-Meteo multi-model)"
        )

    impacts = facts.get("impacts") or {}
    if impacts:
        lines.append(
            "HISTORICAL IMPACTS: " + f"{_num(impacts.get('n_events'), '{:.0f}')} documented events"
        )
        for ev in impacts.get("events", [])[:8]:
            lines.append(
                f"  - {ev.get('event_name', '?')} [{ev.get('hazard_type', '?')}, "
                f"{ev.get('start_date', '?')}]: {ev.get('reported_impacts', '')}"
            )

    water = facts.get("water") or {}
    if water:
        lines.append(f"WATER: {water.get('note', '')}")
        if water.get("available_inputs"):
            lines.append(f"  available inputs: {', '.join(water['available_inputs'])}")
        if water.get("missing_inputs"):
            lines.append(f"  missing inputs: {', '.join(water['missing_inputs'])}")

    pop = facts.get("population") or {}
    if pop:
        lines.append(
            "POPULATION EXPOSURE: "
            + f"WorldPop {_num(pop.get('population'), '{:.0f}')} "
            + f"within {_num(pop.get('radius_km'), '{:.0f}')} km"
            + (f" (zonal {_num(pop.get('zonal'), '{:.0f}')})" if pop.get("zonal") else "")
        )

    if not lines:
        return "No data available for this location."

    lines.append(
        "NOTE: values are real computed/live data; n/a means missing. Baseline is 1991–2020."
    )
    return "\n".join(lines)
