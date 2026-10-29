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
* **El Niño Comparison page** — long ERA5 series (1997→now) per location vs the
  2015-16 / 1997-98 / 2023-24 emergencies; sourced crisis facts + media links.
* **AI Analysis (sandboxed)** — LLM chat grounded in a deterministic data snapshot;
  read-only text pipe (no tools/code execution), bounded input/output.
* **Satellite basemaps** — folium Leaflet maps over Esri World Imagery + NASA GIBS
  (replaces Plotly `scattergeo`).
* **WeatherNext 3 + NVIDIA Earth-2** — credential-gated adapters wired honestly
  (`requires_credentials`); WeatherNext access form submitted (monitor running).

## v0.3.0 (2026-10-29) — polygons, PEAC, remote-sensing, macOS app

1. **Map polygon rendering + area-weighted aggregation** — administrative boundary
   polygons (FSM/RMI HDX COD-AB + Palau geoBoundaries) rendered on the folium map;
   `polygon_area_km2()` (spherical, hole-aware) and `aggregate_by_area()` correct
   the simple mean where island sizes differ. 27 entities matched to polygons
   (countries = ADM0, outer islands = not ADM1 — documented).
2. **PEAC seasonal rainfall outlook** — scraped weather.gov/peac into per-station
   tercile outlooks (7 FAS stations carry geo_ids), with a **freshness guard**
   (product is stale: last updated 2024-09-16, SON 2024; the PEU newsletter is
   discontinued) so it is shown as historical, never current.
3. **SST + chlorophyll-a overlays** — MUR SST, MUR SST anomaly, and PACE OCI
   chlorophyll-a as keyless GIBS WMTS overlays (layer IDs/TMS verified live).
4. **macOS app + offline cache (final phase)** — SwiftUI shell (`apps/macos/`)
   hosting the Streamlit app in a WKWebView, with `COFA_OFFLINE` snapshot mode:
   `FileCache(serve_stale=True)`, `data/raw/` persistence, and a structured
   `data/snapshot/` store + `scripts/prefetch_snapshot.py` + `deploy_macos_app.sh`.

## v0.3.1 (2026-10-29) — IMERG live-verify + offline basemap tiles

* **IMERG live-verified** — the EDL bearer token works (`search_data` returns
  granules for both Final Run historical and Early Run near-real-time). Added
  `imerg.ensure_earthdata_token()` (auto-loads `~/.config/cofa-forward/earthdata_token`)
  and a `product` selector (`final`/`early`/`late`) fixing the near-real-time vs
  Final-Run-lag mismatch. The `test_live_imerg_daily` network test passes.
* **Offline basemap tiles** — `visualization/tiles.py` (OSM XYZ tile math +
  prefetch), `scripts/prefetch_tiles.py`, and `cofa_forward.tileserver` (stdlib
  loopback tile server on :8502). Offline mode swaps the OSM basemap to the local
  server; the macOS app launches the tile server automatically.

## Next (prioritized)

1. **USGS western-Pacific drought (P1RXUMV3)** — manual browser import
   (ScienceBase bot-blocks); covers FSM/RMI (not Palau).
2. Himawari IR bands + region-zoom tiles (visible full-disk only today).
3. Offline satellite tiles (Esri ToS / GIBS low zoom means OSM streets is the
   offline imagery; a proper open satellite source would remove this gap).

## Deferred / not attempted

* Palau ADM2 / municipality geometry; area-weighted aggregation is ADM1-only for now.
* Dynamical/statistical downscaling — not implemented (never claimed).
* WeatherNext 3 (allowlist-gated; keep optional). Remote deployment hardening.
