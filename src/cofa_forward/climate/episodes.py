"""Historical ENSO episode catalog and matching."""

from __future__ import annotations

import pandas as pd

from ..schemas import EnsoEpisode


def match_episodes(episodes: list[EnsoEpisode], date) -> list[EnsoEpisode]:
    """Return episodes whose [start, end] window contains ``date``.

    Episodes with missing start/end (e.g. an unconfirmed evolving event) are
    never matched, so we do not imply coverage we don't have.
    """
    ts = pd.Timestamp(date)
    out = []
    for ep in episodes:
        if ep.start is None or ep.end is None:
            continue
        start = pd.Timestamp(ep.start)
        end = pd.Timestamp(ep.end)
        if start <= ts <= end:
            out.append(ep)
    return out


def episodes_in_phase(episodes: list[EnsoEpisode], phase: str) -> list[EnsoEpisode]:
    return [e for e in episodes if e.phase == phase]


def episode_duration_months(ep: EnsoEpisode) -> int | None:
    if ep.start is None or ep.end is None:
        return None
    start = pd.Timestamp(ep.start)
    end = pd.Timestamp(ep.end)
    return (end.year - start.year) * 12 + (end.month - start.month)
