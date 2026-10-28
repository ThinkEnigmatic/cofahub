# Roadmap

## Done (v0.1.0 → v0.2.0)

* Phase 0 — environment, project structure, config, logging, tests, docs.
* Phase 1 — working app shell: 9 pages, seed geography registry, shared map,
  Overview + Island Profiles + Data Health, clearly labeled sample data.
* Phase 2 — live weather integration (Open-Meteo forecast + ERA5 archive),
  caching, validation, provenance, timestamps, graceful failure.
* **ENSO (Phase 3 core)** — live CPC ONI adapter (authoritative index + derived
  phase via CPC criterion), wired into the ENSO & Overview pages.
* **Cyclones (Phase 5 core)** — live IBTrACS v04r01 WP-basin historical tracks +
  JMA RSMC Tokyo active-storm adapter (position, wind, pressure, forecast track).
* **Science** — forecast-verification framework (bias/MAE/RMSE/skill) and full
  gamma-fit SPI (MLE + zero-precipitation handling), both tested.
* **Data-source research** — 5 extensive research passes; all remaining sources
  verified and cataloged (see docs/DATA_SOURCES.md).

## Next (prioritized)

1. **Phase 3 completion** — CPC Diagnostic Discussion scrape (official alert
   status), PEAC seasonal rainfall outlook (freshness-guarded), NMME NetCDF.
2. **Phase 4** — pull real CHIRPS/IMERG precipitation per location (add
   rasterio/xarray); compute SPEI; threshold editing in the UI.
3. **Phase 5 completion** — JTWC text warnings + NWS Guam advisories; wire
   IBTrACS/JMA into the Tropical Cyclones page (currently CLI + tested).
4. **Phase 6** — authoritative impact catalog + FTS5/RAG indexing; PDF export.
5. **Phase 7** — exposure overlays (WorldPop + HDX COD-AB + GEBCO), ECMWF
   AIFS / GFS model comparison, forecast verification vs real archives,
   optional local LLM.

## Deferred / not attempted

* Geometry/boundaries (GeoPandas/Shapely) — point registry for now.
* Dynamical/statistical downscaling — not implemented (never claimed).
* WeatherNext 3 (allowlist-gated; keep optional). Remote deployment hardening.
