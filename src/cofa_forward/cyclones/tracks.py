"""Tropical cyclone track data model and basic statistics.

Real track ingestion (IBTrACS) is Phase 5. This module defines the canonical
track schema and deterministic statistics over a track table, so sample data and
real data flow through the same code path.
"""

from __future__ import annotations

import pandas as pd

TRACK_COLUMNS = ["storm_id", "time", "lat", "lon", "wind_kt", "pressure_hpa", "agency"]


def validate_track_df(df: pd.DataFrame) -> pd.DataFrame:
    """Validate a track DataFrame has the required columns (else raise)."""
    missing = [c for c in TRACK_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Track table missing columns: {missing}")
    return df


def storm_count_by_year(df: pd.DataFrame) -> pd.Series:
    """Distinct storms per calendar year."""
    validate_track_df(df)
    return df.groupby(pd.to_datetime(df["time"]).dt.year)["storm_id"].nunique().sort_index()


def storm_count_by_month(df: pd.DataFrame) -> pd.Series:
    """Distinct storms per calendar month (all years combined)."""
    validate_track_df(df)
    return df.groupby(pd.to_datetime(df["time"]).dt.month)["storm_id"].nunique().sort_index()


def distinct_storms(df: pd.DataFrame) -> list[str]:
    validate_track_df(df)
    return sorted(df["storm_id"].unique().tolist())
