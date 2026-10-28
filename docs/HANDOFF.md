# COFA FORWARD — Handoff (cold-start state)

> Written 2026-10-28. Read this first in any new session to continue without
> re-discovering the project, its data sources, or the environment quirks.

## One-line summary

COFA FORWARD is a local Streamlit weather-intelligence platform for the Freely
Associated States (Palau, FSM, RMI): **Weather Operations** + **Anticipatory
Intelligence** (ENSO-informed drought/cyclone/water analysis) on a shared data +
geospatial foundation. Repo: `~/cofa-forward`.

## Where things stand

- **7 commits**; latest `9db151a`. Git repo is local (no remote).
- **Tests:** 151 offline + 7 live-network pass. Lint/format clean (ruff).
- **App:** 10 pages, all render (AppTest). Live at `http://127.0.0.1:8501`.
- Phases 0–7 of the original build prompt are substantially complete; the only
  remaining data-source gaps are documented in the roadmap (below).

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

## ⚠️ Environment blocker (MUST READ)

**A machine-wide DNS outage hit mid-build and is NOT fully resolved.**

- Root cause: **Tailscale client (1.94.2) is stale vs the daemon (1.104.2)** →
  MagicDNS (resolver `100.100.100.100`) stopped forwarding → the system resolver
  (mDNSResponder) got stuck → `uv` panics (`system-configuration` crate reads a
  NULL) and `curl`/`pip`/`requests` DNS lookups fail.
- **Applied fix:** `tailscale set --accept-dns=false` (reverted system DNS to
  `1.1.1.1`/`8.8.8.8`; reversible with `--accept-dns=true`). This fixed the
  *config* but the resolver daemon remained stuck.
- **Consequences still active:**
  - `uv run/add/sync` **panics**. Use `.venv/bin/python` directly (works).
  - The uv venv has **no `pip`** (`python -m pip` → "No module named pip").
  - **`pyshp` was hand-installed** by extracting the pure-Python wheel into
    `.venv/lib/python3.12/site-packages/shapefile.py`. `pyproject.toml` declares
    `pyshp>=3.1` but **`uv.lock` is stale** (no pyshp entry).
  - No sudo ("you do not exist in the passwd database" — shell runs as UID 501).
- **How to fully restore:** as the machine owner run `brew upgrade tailscale`
  (or restart Tailscale), then `cd ~/cofa-forward && uv sync` to reconcile
  `uv.lock`. Until then, everything still works via `.venv/bin/python`.
- **Download workaround** (if DNS is still flaky): `dig +short @8.8.8.8 <host>`
  then `curl --resolve "<host>:443:<IP>" ...`. HDX downloads also need a
  `--resolve` for `s3.us-east-1.amazonaws.com` (HDX redirects there via
  presigned URL).

## Data sources — status (all verified 2026-10-28)

`implemented_and_tested` (live adapters, in `src/cofa_forward/ingestion/`):

| source_id | module | notes |
|---|---|---|
| open-meteo-forecast | weather.py | current+hourly+daily, 16-day, no key |
| open-meteo-archive | rainfall.py | ERA5 daily precip (climatology/anomalies) |
| noaa-cpc-enso | enso.py | ONI `oni.ascii.txt`; phase via ≥5-season criterion |
| noaa-ibtracs | ibtracs.py | WP-basin CSV (114 MB); WMO wind/pressure |
| jma-rsmc-tokyo | jma.py | active storms `targetTc.json` → `specifications.json` |
| chirps-v3 | chirps.py | monthly COGs via rasterio `/vsicurl/` (land-masked) |
| worldpop-population | population.py | ~1 km UN-adjusted grids; point/radius |
| hdx-cod-ab | boundaries.py | FSM/RMI polygons via pyshp+rasterio; zonal pop |

`planned` (researched, not wired): PEAC seasonal outlook, NMME NetCDF, ECMWF
AIFS, NOAA GFS/GEFS, CPC ENSO Diagnostic Discussion (partly via bulletin
monitor), JTWC/NWS-Guam advisories (partly via bulletin monitor), PERSIANN-CDR,
GPCC, SPEIbase, Copernicus DEM/GEBCO, IMERG (`requires_credentials`), WeatherNext
3 (`unavailable` — allowlist-gated). Full details in `docs/DATA_SOURCES.md`.

## Layout

```
config/            app, geography (seed), sources, enso, drought, cyclones, alerts, bulletins
src/cofa_forward/
  ingestion/       base + 8 live adapters + bulletins monitor + stubs
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

1. **Palau boundaries** — SPC Pacific Data Hub `2015_plw_phc_admin_boundaries`
   (Palau has no COD-AB; currently point-based).
2. **PEAC + NMME** seasonal outlook ingestion.
3. **ECMWF AIFS / GFS** model comparison (GRIB via `ecmwf-opendata`/`cfgrib`).
4. **IMERG** — Earthdata login (`earthaccess`), documented `requires_credentials`.
5. Polish: render boundary polygons on the map; area-weighted aggregation;
   Palau point→polygon migration.

## Gotchas

- `scripts/verify_pages.py` (AppTest) times out when DNS is down because live
  fetches retry slowly; it passed cleanly (10/10) when network was up.
- IBTrACS CSV is ~114 MB; the network test downloads it (marked `network`).
- `monthly_totals` drops timezone before `to_period("M")` (avoids a pandas warning).
- The app's cached helpers (`ui/state.py`) use `st.cache_data` with TTLs — real
  rainfall/CHIRPS/WorldPop/boundaries are fetched once and cached (24h), so first
  load can be slow (CHIRPS full baseline ~1–2 min).
