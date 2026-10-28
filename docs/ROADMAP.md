# Roadmap

## Done (v0.1.0)

* Phase 0 — environment, project structure, config, logging, tests, docs.
* Phase 1 — working app shell: 9 pages, seed geography registry, shared map,
  Overview + Island Profiles + Data Health, clearly labeled sample data.
* Phase 2 — live weather integration (Open-Meteo forecast + ERA5 archive),
  caching, validation, provenance, timestamps, graceful failure.

## Next (prioritized)

1. **Phase 3 — ENSO & climate foundation**
   * CPC ONI ingestion (authoritative ENSO state + outlook).
   * Pull ERA5 archive per location to build real climatology/anomalies.
   * Wire the historical analog engine to real data.
2. **Phase 4 — drought & freshwater**
   * Full gamma-fit SPI (validated).
   * Threshold editing in the UI.
3. **Phase 5 — tropical cyclones**
   * IBTrACS ingestion; real track visualization + proximity + ENSO-conditioned
     analysis; official advisory integration.
4. **Phase 6 — impacts & reports**
   * Authoritative impact catalog ingestion + FTS5/RAG indexing.
   * PDF export for the daily brief.
5. **Phase 7 — integration**
   * Richer overlays, exports, model comparison (WeatherNext if approved),
     optional local LLM, forecast-verification framework, more tests.

## Deferred / not attempted

* Geometry/boundaries (GeoPandas/Shapely) — point registry for now.
* Dynamical/statistical downscaling — not implemented (never claimed).
* Remote deployment hardening (see SECURITY.md).
