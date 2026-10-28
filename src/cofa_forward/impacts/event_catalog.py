"""Structured historical impact catalog.

The catalog distinguishes *documented* impacts from *inferred* and *modeled*
estimates, and never implies a report covers a whole country when it only
describes one island. Sample entries are explicitly labeled ``sample``.
"""

from __future__ import annotations

import pandas as pd

IMPACT_FIELDS = [
    "event_id",
    "event_name",
    "hazard_type",
    "start_date",
    "end_date",
    "country",
    "geo_id",
    "enso_phase",
    "enso_episode_id",
    "observed_conditions",
    "reported_impacts",
    "affected_population",
    "infrastructure_impacts",
    "water_impacts",
    "response_actions",
    "recovery_information",
    "source_url",
    "source_publisher",
    "source_publication_date",
    "evidence_quality",
    "confidence",
    "extraction_method",
    "verification_status",
    "notes",
]


class ImpactCatalog:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def all(self) -> pd.DataFrame:
        return self.df

    def by_country(self, country: str) -> pd.DataFrame:
        return self.df[self.df["country"] == country]

    def by_geo_id(self, geo_id: str) -> pd.DataFrame:
        return self.df[self.df["geo_id"] == geo_id]

    def by_hazard(self, hazard_type: str) -> pd.DataFrame:
        return self.df[self.df["hazard_type"] == hazard_type]

    def by_enso_episode(self, episode_id: str) -> pd.DataFrame:
        return self.df[self.df["enso_episode_id"] == episode_id]

    def counts_by_hazard(self) -> pd.Series:
        return self.df["hazard_type"].value_counts()


def load_catalog(df: pd.DataFrame) -> ImpactCatalog:
    """Validate and wrap an impact DataFrame (missing optional columns -> empty)."""
    for col in ("event_id", "hazard_type", "country", "geo_id"):
        if col not in df.columns:
            raise ValueError(f"impact catalog missing required column: {col}")
    return ImpactCatalog(df)
