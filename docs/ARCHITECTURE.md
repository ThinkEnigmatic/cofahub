# Architecture

COFA FORWARD is a modular Python application (Streamlit UI) for weather
operations and anticipatory climate intelligence over the Freely Associated
States (Palau, FSM, RMI). It is a single-developer-friendly, single-process app
with no microservices and no required credentials.

## Design principles

1. **One data foundation, two modes.** Weather Operations and Anticipatory
   Intelligence share the same geographic registry, observations/forecasts,
   source/timestamp metadata, map framework, island profiles, impact catalog,
   and uncertainty framework.
2. **Deterministic science first.** Every quantitative indicator is a tested
   numerical function. A language model (optional, not enabled by default) may
   only *explain* validated results — never compute them.
3. **Provenance everywhere.** Derived values record their inputs, methods,
   parameters, baselines, aggregation, and missing-data handling.
4. **Never fabricate.** Missing data stays missing; no invented storms,
   warnings, forecasts, probabilities, or impact counts.

## Package layout

```
config/          YAML (app, geography, sources, enso, drought, cyclones, alerts)
src/cofa_forward/
  config.py        validated config loader (pydantic-backed schemas)
  units.py         explicit metric<->imperial conversions
  timeutil.py      UTC timestamp normalization
  schemas.py       pydantic models (GeoEntity, SourceRecord, EnsoEpisode, ...)
  sample_data.py   deterministic synthetic sample data (clearly labeled)
  ingestion/       provider adapters (base + Open-Meteo forecast/archive + stubs)
  storage/         FileCache, SQLite Database, ParquetStore, provenance
  geography/       registry, spatial attribution (haversine), aggregation
  climate/         ENSO state, episodes, analogs, climatology
  drought/         rainfall metrics, anomalies, percentiles, SPI, freshwater, alerts
  cyclones/        tracks, proximity, climatology, ENSO analysis, exposure
  impacts/         event catalog, evidence labeling
  intelligence/    indicators, synthesis, confidence, report builder
  visualization/   maps (Plotly scattergeo), charts, legends, layers
  ui/              Streamlit app + 9 pages + shared components
scripts/          initialize_data, ingest_weather, ingest_rainfall, ...
tests/            unit + integration + scientific regression (pytest)
```

## Data flow

```
providers --(ingestion adapters)--> FileCache --> normalize/validate
      |                                    |
      +-- provenance/ingestion history --> SQLite (data/catalog.db)
                                           |
computed indicators/analogs <-- drought/climate/cyclone modules
      |
      +--> ui/ (Streamlit) & intelligence/report_builder (Markdown brief)
```

* `data/raw` — untouched source data
* `data/interim` — intermediate transforms
* `data/processed` — normalized analytical datasets
* `data/samples` — clearly labeled synthetic data
* `data/cache` — TTL cache for remote fetches

## Key decisions

* **Maps use Plotly `scattergeo`** (no Mapbox token, no tile API key) so the app
  runs fully offline with built-in Natural Earth coastlines. A heavier map stack
  (PyDeck/Folium) is a later option if richer base layers are needed.
* **Geography is point-based seed data.** Boundaries/polygons (GeoPandas/Shapely)
  are deferred; the registry is data-driven so a validated inventory can replace
  the seed YAML without code changes.
* **Spatial attribution is nearest-grid-cell**, recorded explicitly, and never
  described as downscaling.
* **Percentile drought indicators before SPI.** A non-parametric normal-score
  SPI is available; full gamma-fit SPI is deferred.

## Extending

Add a provider: subclass `ingestion.base.BaseAdapter`, implement `fetch`/
normalization, add a row to `config/sources.yaml`, and set its status honestly.
Add a location: append an entity to `config/geography.yaml`.
