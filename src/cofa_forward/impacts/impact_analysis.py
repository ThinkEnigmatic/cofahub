"""Impact analysis: summaries and ENSO association."""

from __future__ import annotations

import pandas as pd

from .event_catalog import ImpactCatalog


def summarize_by_country(catalog: ImpactCatalog) -> pd.DataFrame:
    """Count impact events by country and hazard type."""
    df = catalog.all()
    return (
        df.groupby(["country", "hazard_type"])["event_id"].count().rename("n_events").reset_index()
    )


def summarize_by_enso_episode(catalog: ImpactCatalog) -> pd.DataFrame:
    """Count impact events associated with each ENSO episode (where recorded)."""
    df = catalog.all()
    if "enso_episode_id" not in df.columns:
        return pd.DataFrame(columns=["enso_episode_id", "n_events"])
    return (
        df.dropna(subset=["enso_episode_id"])
        .groupby("enso_episode_id")["event_id"]
        .count()
        .rename("n_events")
        .reset_index()
    )


def impacts_for_analog(catalog: ImpactCatalog, episode_id: str) -> pd.DataFrame:
    """Return documented impacts for a historical ENSO episode."""
    return catalog.by_enso_episode(episode_id)
