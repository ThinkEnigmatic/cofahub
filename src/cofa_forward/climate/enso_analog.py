"""ENSO analog selection from the live ONI record.

Ranks historical El Niño/La Niña episodes by how closely their peak ONI
anomaly matches the current value, so the app can say "this event most
resembles 1997-98 / 2015-16" and point at what those did in the FAS (the
El Niño Comparison page). Purely numerical, explainable, and only compares
same-phase episodes — a historical analog is contextual evidence, never a
forecast.
"""

from __future__ import annotations

import pandas as pd

from ..schemas import EnsoEpisode


def episode_peak_oni(episode: EnsoEpisode, oni: pd.DataFrame) -> float | None:
    """Peak absolute ONI anomaly (°C) within the episode's date window."""
    if episode.start is None or episode.end is None:
        return None
    start = pd.Timestamp(episode.start)
    end = pd.Timestamp(episode.end)
    dates = pd.to_datetime(oni["date"])
    win = oni.loc[(dates >= start) & (dates <= end), "anom"]
    if win.empty:
        return None
    return float(win.abs().max())


def enso_analogs(
    current_phase: str,
    current_oni: float,
    episodes: list[EnsoEpisode],
    oni: pd.DataFrame,
    top_n: int = 3,
) -> list[dict]:
    """Rank same-phase historical episodes by peak-ONI proximity to the current value.

    Returns a list of ``{episode_id, intensity, peak_oni, similarity}`` sorted by
    similarity (1 = identical peak). ``similarity = 1 / (1 + |Δ ONI|)`` — a
    documented, monotone proximity score, not a probability.
    """
    out = []
    for ep in episodes:
        if ep.phase != current_phase:
            continue
        peak = episode_peak_oni(ep, oni)
        if peak is None:
            continue
        diff = abs(current_oni - peak)
        out.append(
            {
                "episode_id": ep.id,
                "intensity": ep.intensity,
                "peak_oni": peak,
                "delta_oni": round(diff, 2),
                "similarity": round(1.0 / (1.0 + diff), 3),
                "start": ep.start,
                "end": ep.end,
            }
        )
    out.sort(key=lambda x: x["similarity"], reverse=True)
    return out[:top_n]
