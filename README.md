# COFA FORWARD

**Weather Operations & Anticipatory Climate Intelligence** for the Freely
Associated States (FAS) of the western tropical Pacific — the Republic of Palau,
the Federated States of Micronesia (FSM), and the Republic of the Marshall
Islands (RMI).

A local, private, extensible Streamlit application that combines general-purpose
weather monitoring (**Weather Operations**) with ENSO-informed anticipatory
analysis (**Anticipatory Intelligence**) on a shared data and geospatial
foundation.

> **Status: initial release (v0.1.0).** This is a working, tested vertical
> slice. Phase 0–2 of the build plan are complete. Later phases (ENSO live
> ingestion, IBTrACS, IMERG, exposure overlays, optional LLM) are documented but
> not yet wired in. See `docs/ROADMAP.md`.

## Quick start

```bash
cd cofa-forward
uv sync                          # create the virtualenv + install deps
source .venv/bin/activate        # activate (or use `uv run ...`)

# Run the test suite (offline; no network, no credentials)
uv run pytest

# Launch the application
uv run streamlit run src/cofa_forward/ui/app.py
# → http://127.0.0.1:8501
```

No credentials are required to launch. The app opens in **sample mode** with
clearly labeled synthetic data and an empty-but-honest state for live sources.

## Features (implemented & tested)

- **9-section navigation**: Overview, Weather Operations, ENSO & Climate,
  Drought & Water, Tropical Cyclones, Historical Impacts, Island Profiles,
  Reports, Data Sources & System Health.
- **FAS geographic registry** (seed, approximate — see `config/geography.yaml`)
  covering the 3 countries, 4 FSM states, and representative islands/atolls.
- **Live weather forecast integration** via Open-Meteo (no API key) with
  caching, provenance, timestamps, and graceful failure handling.
- **Historical rainfall / climatology** via the Open-Meteo ERA5 archive
  (Phase 3 groundwork; adapter tested).
- **Deterministic scientific modules**: unit conversion, rolling rainfall
  totals, anomalies, empirical percentiles, SPI, spatial attribution,
  cyclone proximity (haversine), ENSO episode matching, historical analog
  scoring, alert-threshold evaluation, provenance records, and a
  deterministic (non-LLM) report generator.

## Layout

```
config/    YAML configuration (app, geography, sources, enso, drought, cyclones, alerts)
src/cofa_forward/
  ingestion/    data-provider adapters (Open-Meteo forecast + archive, stubs)
  storage/      cache, provenance, parquet, sqlite catalog
  geography/    registry, spatial attribution, aggregation
  climate/      ENSO state, episodes, analogs, climatology
  drought/      rainfall metrics, anomalies, percentiles, SPI, freshwater, alerts
  cyclones/     tracks, proximity, climatology, exposure
  impacts/      event catalog, evidence
  intelligence/ indicators, synthesis, report builder
  visualization/ maps, charts, legends
  ui/           Streamlit app + pages
tests/         unit + integration + scientific regression tests
docs/          architecture, data sources, data dictionary, methods, roadmap
```

See `docs/ARCHITECTURE.md` for the full design.
