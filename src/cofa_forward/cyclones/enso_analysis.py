"""ENSO-conditioned cyclone analysis.

Reports counts by ENSO phase WITH sample sizes and explicit limitations. We do
not claim a causal relationship from a correlation, and we do not hard-code a
multiplier into an operational risk probability.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def phase_storm_counts(
    events: pd.DataFrame,
    storm_col: str = "storm_id",
    phase_col: str = "enso_phase",
) -> dict[str, Any]:
    """Count distinct storms (and events) per ENSO phase.

    ``events`` is a per-storm table with at least ``storm_col`` and ``phase_col``.
    Returns counts plus the sample size (number of storms) per phase.
    """
    if storm_col not in events.columns or phase_col not in events.columns:
        raise ValueError("events must include storm and phase columns")

    counts = (
        events.drop_duplicates(subset=[storm_col]).groupby(phase_col)[storm_col].count().to_dict()
    )
    return {
        "storm_counts": counts,
        "n_total_storms": int(events[storm_col].nunique()),
        "n_total_events": int(len(events)),
        "sample_sizes": {k: int(v) for k, v in counts.items()},
        "note": (
            "Counts are descriptive and phase-labeled by a configured association. "
            "Small samples and observation-system changes over time limit inference; "
            "no causal claim is implied."
        ),
    }


def phase_proximity_rates(
    registry_locations: list[tuple[str, float, float]],
    track_df: pd.DataFrame,
    phase_series: pd.Series,
    radius_km: float = 300,
) -> dict[str, Any]:
    """Proximity-exposure rates by ENSO phase (skeleton; requires phase-mapped tracks).

    ``phase_series`` maps storm_id -> ENSO phase. This is a proximity estimate,
    not a wind-impact estimate. Returns per-phase counts of storms passing
    within ``radius_km`` of any location.
    """
    from .proximity import closest_approach

    phase_map = phase_series.to_dict()
    storms = track_df["storm_id"].unique()
    per_phase: dict[str, int] = {}
    total_any = 0
    for sid in storms:
        sub = track_df[track_df["storm_id"] == sid]
        within = any(
            closest_approach(lat, lon, sub)
            and closest_approach(lat, lon, sub)["distance_km"] <= radius_km
            for _, lat, lon in registry_locations
        )
        if within:
            total_any += 1
            ph = phase_map.get(sid, "unknown")
            per_phase[ph] = per_phase.get(ph, 0) + 1
    return {
        "radius_km": radius_km,
        "per_phase": per_phase,
        "n_total_storms": int(len(storms)),
        "n_within_radius": total_any,
        "note": "Proximity exposure only; not a wind-impact or risk probability.",
    }
