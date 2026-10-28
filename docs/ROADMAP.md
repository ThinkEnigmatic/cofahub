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
* **CHIRPS v3 precipitation** — point extraction from monthly COGs (rasterio
  range requests); land-masked heuristic documented; wired into Drought page.
* **WorldPop population** — ~1 km population grids (point/radius extraction),
  wired into Island Profiles as a spatial-exposure layer.
* **Water-need forecast (micro level)** — deterministic modeled water balance per
  island/atoll: population → demand → required rainfall vs forecast → projected
  deficit/surplus, with documented planning-default assumptions and a new
  "Water Need Forecast" page.
* **Bulletin monitor** — polls public bulletins (NWS Guam, JTWC, JMA, CPC ENSO),
  detects new/updated content by hash, parses structured summaries (incl. the
  official CPC ENSO alert status), snapshots raw text, and logs updates to the
  dataset dynamically (CLI + UI feed + scheduling doc).
* **Administrative boundaries** — FSM/RMI via HDX COD-AB (pyshp+rasterio) and
  Palau via geoBoundaries (GeoJSON); accurate zonal WorldPop population wired
  into Island Profiles (fixes the point+radius undercount for all 3 countries).
* **NMME seasonal forecasts** — 6-model ensemble (xarray + netCDF4), wired into
  the ENSO & Climate page as a multi-model precipitation outlook.
* **Model comparison** — Open-Meteo multi-model API (ECMWF IFS/AIFS, GFS, ICON,
  GEM, …) wired into Weather Operations; no GRIB/eccodes needed.

## Next (prioritized)

1. **IMERG** — Earthdata login (`earthaccess`), documented `requires_credentials`.
2. Palau geometry refinement / area-weighted aggregation / map polygon rendering.

## Deferred / not attempted

* Palau geometry (no COD-AB); area-weighted aggregation; full map polygon rendering.
* Dynamical/statistical downscaling — not implemented (never claimed).
* WeatherNext 3 (allowlist-gated; keep optional). Remote deployment hardening.
