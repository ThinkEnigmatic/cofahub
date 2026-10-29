"""Pydantic schemas for structured configuration and records."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Geography
# --------------------------------------------------------------------------- #

EntityType = Literal["country", "state", "island", "atoll", "monitoring_location"]


class GeoEntity(BaseModel):
    geo_id: str
    name: str
    entity_type: EntityType
    country_code: str
    parent_geo_id: str | None = None
    latitude: float
    longitude: float
    geometry_path: str | None = None
    area_km2: float | None = None
    population: int | None = None
    population_year: int | None = None
    population_source: str | None = None
    airport: str | None = None
    port: str | None = None
    elevation_source: str | None = None
    data_coverage: str | None = None
    spatial_resolution_notes: str | None = None
    metadata_source: str | None = None
    notes: str | None = None


# --------------------------------------------------------------------------- #
# Data sources
# --------------------------------------------------------------------------- #

SourceStatus = Literal[
    "implemented_and_tested",
    "implemented_but_not_verified",
    "requires_credentials",
    "requires_manual_import",
    "planned",
    "unavailable",
]


class SourceRecord(BaseModel):
    id: str
    name: str
    publisher: str
    url: str
    api: str | None = None
    license: str | None = None
    geographic_coverage: str | None = None
    spatial_resolution: str | None = None
    temporal_resolution: str | None = None
    update_frequency: str | None = None
    auth: str | None = None
    variables: str | None = None
    limitations: str | None = None
    implementation_status: SourceStatus
    verification_date: str | None = None
    notes: str | None = None


# --------------------------------------------------------------------------- #
# ENSO
# --------------------------------------------------------------------------- #


class EnsoEpisode(BaseModel):
    id: str
    phase: str | None = None
    start: str | None = None
    peak: str | None = None
    end: str | None = None
    intensity: str | None = None
    verification_status: str = "seed_approximate"
    note: str | None = None


# --------------------------------------------------------------------------- #
# Alerts
# --------------------------------------------------------------------------- #


class AlertThreshold(BaseModel):
    id: str
    name: str
    indicator: str
    geographic_scope: str = "all"
    comparison_baseline: str | None = None
    threshold: dict[str, Any] = Field(default_factory=dict)
    persistence_months: int = 0
    forecast_horizon: str | None = None
    data_source: str | None = None
    confidence_requirement: str = "any"
    responsible: str | None = None
    created: str | None = None
    note: str | None = None


# --------------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------------- #


class ProvenanceRecord(BaseModel):
    record_id: str | None = None
    dataset_id: str | None = None
    source_url: str | None = None
    retrieved_at: str | None = None
    valid_time: str | None = None
    init_time: str | None = None
    lead_time: str | None = None
    calculation_method: str | None = None
    parameters: dict[str, Any] | None = None
    baseline_period: str | None = None
    geographic_aggregation: str | None = None
    missing_data_handling: str | None = None
    output_timestamp: str | None = None
    code_version: str | None = None
    notes: str | None = None
