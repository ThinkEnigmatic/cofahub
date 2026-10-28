# COFA FORWARD — Handoff (cold-start state)

> Written 2026-10-28. Read this first in any new session to continue without
> re-discovering the project, its data sources, or the environment quirks.

## One-line summary

COFA FORWARD is a local Streamlit weather-intelligence platform for the Freely
Associated States (Palau, FSM, RMI): **Weather Operations** + **Anticipatory
Intelligence** (ENSO-informed drought/cyclone/water analysis) on a shared data +
geospatial foundation. Repo: `~/cofa-forward`.

## Where things stand

- **14 commits**; latest `3f4c5fa`. Git repo is local (no remote).
- **Tests:** 162 offline + 10 live-network pass. Lint/format clean (ruff).
- **App:** 10 pages, all render (AppTest). Live at `http://127.0.0.1:8501`.
- Phases 0–7 of the original build prompt are substantially complete; the only
  remaining item is IMERG live-verification (needs Earthdata credentials).

## Commands

```bash
cd ~/cofa-forward

# tests (use .venv/bin/python directly — uv is currently broken, see below)
.venv/bin/python -m pytest -m "not network" -q     # offline (151)
.venv/bin/python -m pytest -m network -q           # live (7, needs internet)

# lint / format
.venv/bin/ruff check . ; .venv/bin/ruff format .

# launch (works via .venv directly)
.venv/bin/streamlit run src/cofa_forward/ui/app.py   # -> http://127.0.0.1:8501

# page-render smoke test (AppTest; slow if DNS is down — times out on live fetches)
.venv/bin/python scripts/verify_pages.py

# CLI
.venv/bin/python scripts/ingest_weather.py --geo PAL-KOR
.venv/bin/python scripts/ingest_enso.py
.venv/bin/python scripts/ingest_ibtracs.py
.venv/bin/python scripts/ingest_jma.py
.venv/bin/python scripts/ingest_chirps.py --geo PAL-KOR
.venv/bin/python scripts/monitor_bulletins.py
.venv/bin/python scripts/check_sources.py
.venv/bin/python scripts/generate_report.py
```

## ⚠️ Environment note (RESOLVED 2026-10-28)

A machine-wide DNS outage hit mid-build and has since been **resolved**. Kept for
reference:

- Root cause was: **Tailscale client (1.94.2) stale vs daemon (1.104.2)** → MagicDNS
  (resolver `100.100.100.100`) stopped forwarding → system resolver stuck → `uv`
  panicked (`system-configuration` crate reads a NULL) and `curl`/`pip`/`requests`
  DNS lookups failed.
- Fix applied: `tailscale set --accept-dns=false` (reverted system DNS to
  `1.1.1.1`/`8.8.8.8`); the machine owner later upgraded Tailscale.
- **Current status: `uv` works, DNS resolves, `uv.lock` is reconciled (pyshp is
  in it).** `uv run pytest`, `uv sync`, `uv run streamlit` all work normally.
- If `uv` ever panics again with `system-configuration … Attempted to create a
  NULL object`, it is the same network/Tailscale issue — check `tailscale status`
  for a client/daemon version mismatch and upgrade/restart Tailscale.
- No sudo available ("you do not exist in the passwd database" — shell runs as
  UID 501). Download workaround (if DNS is ever flaky): `dig +short @8.8.8.8
  <host>` then `curl --resolve "<host>:443:<IP>" ...`. HDX downloads also need a
  `--resolve` for `s3.us-east-1.amazonaws.com` (HDX redirects there via presigned
  URL).

## Data sources — status (all verified 2026-10-28)

`implemented_and_tested` (live adapters, in `src/cofa_forward/ingestion/`):

| source_id | module | notes |
|---|---|---|
| open-meteo-forecast | weather.py | current+hourly+daily, 16-day, no key; **multi-model** (`models=`) |
| open-meteo-archive | rainfall.py | ERA5 daily precip (climatology/anomalies) |
| noaa-cpc-enso | enso.py | ONI `oni.ascii.txt`; phase via ≥5-season criterion |
| noaa-ibtracs | ibtracs.py | WP-basin CSV (114 MB); WMO wind/pressure |
| jma-rsmc-tokyo | jma.py | active storms `targetTc.json` → `specifications.json` |
| chirps-v3 | chirps.py | monthly COGs via rasterio `/vsicurl/` (land-masked) |
| worldpop-population | population.py | ~1 km UN-adjusted grids; point/radius |
| hdx-cod-ab | boundaries.py | FSM/RMI polygons via pyshp+rasterio; zonal pop |
| geoboundaries | boundaries.py | Palau ADM1 (16 states, ODbL/OSM) via GeoJSON |
| noaa-nmme | nmme.py | 6-model seasonal ENSMEAN (xarray + netCDF4) |

`implemented_but_not_verified` (adapter + mocks, needs credentials):

| nasa-gpm-imerg | imerg.py | earthaccess daily point extraction (Earthdata login) |

`planned` (researched, not wired): PEAC seasonal outlook, CPC ENSO Diagnostic
Discussion (partly via bulletin monitor), JTWC/NWS-Guam advisories (partly via
bulletin monitor), PERSIANN-CDR, GPCC, SPEIbase, Copernicus DEM/GEBCO, WeatherNext
3 (`unavailable` — allowlist-gated). Full details in `docs/DATA_SOURCES.md`.

## Layout

```
config/            app, geography (seed), sources, enso, drought, cyclones, alerts, bulletins
src/cofa_forward/
  ingestion/       base + 10 live adapters + bulletins monitor + IMERG (needs creds) + stubs
  storage/         FileCache, SQLite Database (provenance/bulletins), parquet, provenance
  geography/       registry (points), spatial_attribution (haversine), aggregation
  climate/         enso_state, episodes, analogs, climatology
  drought/         rainfall_metrics, anomalies, percentiles, spi (gamma), water_balance, alerts
  cyclones/        tracks, proximity, climatology, enso_analysis, exposure
  impacts/         event_catalog, evidence
  intelligence/    indicators, synthesis, confidence, report_builder, verification
  visualization/   maps (plotly scattergeo), charts, legends, layers
  ui/              app.py + 10 pages + components + state.py (cached loaders)
scripts/           12 CLI scripts
tests/             unit/ + integration/ (network-marked) + fixtures/
data/              raw/ (worldpop, boundaries, bulletins) · processed/ · samples/ · cache/ · catalog.db
```

## Key scientific/engineering decisions (do not regress)

1. **Never fabricate.** Missing data stays missing; no invented storms/warnings/
   probabilities/impact counts. ENSO phase is derived from ONI and labeled as
   derived (official status = CPC discussion, ingested by the bulletin monitor).
2. **Provenance everywhere.** Derived values carry dataset/timestamp/method/
   baseline/aggregation. Stored in SQLite `data/catalog.db`.
3. **Units:** metric for science, imperial presentation-only (`units.py`).
4. **Spatial attribution ≠ downscaling.** Nearest-grid-cell only; the app always
   says "regional model estimate; individual-atoll conditions may differ."
5. **Percentile indicators before SPI** (gamma SPI now implemented in
   `drought/spi.py` — validated against reference values).
6. **Water balance is modeled** (`drought/water_balance.py`): documented planning
   defaults (100 L/person/day, 10 m²/person catchment, 0.8 eff), never claims
   actual shortage.
7. **CHIRPS land-mask heuristic:** max-valid-pixel in a 5×5 window (documented;
   ERA5 preferred for ocean-adjacent atolls).
8. **WorldPop is UN-adjusted** — use zonal (boundary) sum as the accurate method;
   census seed figures are the atoll total of record.
9. **Map = Plotly `scattergeo`** (no Mapbox token / tile key). Boundaries are not
   yet rendered as polygons on the map (only used for zonal stats).

## Cached data on disk (gitignored, already present)

- `data/raw/worldpop/{mhl,fsm,plw}_2020.tif` (WorldPop 1 km grids)
- `data/raw/boundaries/{mhl,fsm}/` (extracted HDX COD-AB SHP)
- `data/raw/bulletins/` (monitor snapshots)
- `data/catalog.db` (SQLite: provenance, ingestion history, bulletins)

## Roadmap (next iteration)

1. **Complete IMERG** — token auth + CMR search are verified; the remaining step is
   a **one-time GPM IMERG EULA acceptance** (browser) at
   `https://urs.earthdata.nasa.gov/approve_app?client_id=e2WVk8Pw6weeLUKZYOxvTQ`
   (the token is stored at `~/.config/cofa-forward/earthdata_token`, 0600).
2. **PEAC seasonal outlook** — HTML scrape (weather.gov/peac); the rainfall
   outlook appeared stale (SON-2024) in research, so add a freshness guard.
3. Polish: render boundary polygons on the map; area-weighted aggregation.

## Gotchas

- `scripts/verify_pages.py` (AppTest) times out when DNS is down because live
  fetches retry slowly; it passed cleanly (10/10) when network was up.
- IBTrACS CSV is ~114 MB; the network test downloads it (marked `network`).
- `monthly_totals` drops timezone before `to_period("M")` (avoids a pandas warning).
- The app's cached helpers (`ui/state.py`) use `st.cache_data` with TTLs — real
  rainfall/CHIRPS/WorldPop/boundaries are fetched once and cached (24h), so first
  load can be slow (CHIRPS full baseline ~1–2 min).
