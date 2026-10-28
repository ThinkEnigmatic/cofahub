"""Tropical cyclone climatology helpers."""

from __future__ import annotations

import pandas as pd

from .tracks import storm_count_by_month, storm_count_by_year, validate_track_df


def seasonal_summary(df: pd.DataFrame, start_month: int = 6, end_month: int = 12) -> dict:
    """Storm counts by year and by month for a basin season window."""
    validate_track_df(df)
    by_year = storm_count_by_year(df)
    by_month = storm_count_by_month(df)
    return {
        "by_year": by_year,
        "by_month": by_month,
        "season_months": list(range(start_month, end_month + 1)),
        "n_storms": df["storm_id"].nunique(),
        "n_points": len(df),
        "year_min": int(df["time"].dt.year.min()),
        "year_max": int(df["time"].dt.year.max()),
    }
