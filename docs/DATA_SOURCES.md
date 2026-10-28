# Data Sources

Status values: `implemented_and_tested`, `implemented_but_not_verified`,
`requires_credentials`, `requires_manual_import`, `planned`, `unavailable`.
A source is marked `implemented_and_tested` only after a successful integration
test. This catalog was refreshed with extensive online research on 2026-10-28
(five independent research passes over ENSO, cyclones, precipitation/drought,
exposure/terrain, and AI-forecast access).

## Implemented & tested (live adapters)

| Source | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| **Open-Meteo Forecast** | `api.open-meteo.com/v1/forecast` | none | current + hourly + daily, 16-day horizon, ~11 km; **multi-model** via `models=` (ECMWF IFS/AIFS, GFS, ICON, GEM) |
| **Open-Meteo Historical (ERA5)** | `archive-api.open-meteo.com/v1/archive` | none | daily precipitation, ~25 km |
| **NOAA CPC Oceanic Niño Index** | `cpc.ncep.noaa.gov/data/indices/oni.ascii.txt` | none | authoritative ENSO index; phase derived via CPC ≥5-season criterion |
| **IBTrACS v04r01 (WP basin)** | `ncei.noaa.gov/.../csv/ibtracs.WP.list.v04r01.csv` | none | historical tracks, 1842–present (114 MB CSV) |
| **JMA RSMC Tokyo (active storms)** | `jma.go.jp/bosai/typhoon/data/targetTc.json` → `specifications.json` | none | position, 10-min wind, pressure, 5-day forecast + probability circles |
| **CHIRPS v3 (precipitation)** | `data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/cogs/` | none | monthly COGs, 0.05°, point extraction via rasterio range requests |

Run them: `scripts/ingest_weather.py`, `ingest_rainfall.py`, `ingest_enso.py`,
`ingest_ibtracs.py`, `ingest_jma.py`, `check_sources.py`. Live tests:
`uv run pytest -m network` (6 tests, all passing).

## ENSO & seasonal climate

* **CPC ONI** (`oni.ascii.txt`) — the canonical index. Free, no auth, plain ASCII,
  monthly, 1950–present. **Implemented.**
* **CPC ENSO Diagnostic Discussion** (`enso_advisory/ensodisc.html`) — the official
  status statement (Watch/Advisory) + probabilistic outlook. Narrative HTML, monthly
  (~2nd Thursday). *Planned* (regex-scrape alert status + synopsis).
* **PEAC** (`weather.gov/peac/`) — FAS-specific seasonal rainfall outlook
  (14 stations incl. Koror/Yap/Chuuk/Pohnpei/Kosrae/Kwajalein/Majuro), monthly.
  HTML tables; *note: fetched page still showed SON-2024 → add a freshness guard*.
* **NMME** (`ftp.cpc.ncep.noaa.gov/International/nmme/netcdf/`) — gridded 1° seasonal
  forecasts (NetCDF3), monthly inits, 2011–present. **Implemented** (xarray +
  netCDF4, 6-model ensemble mean + spread, wired into ENSO & Climate page).
  IRI Data Library now requires login; CPC FTP + AWS `s3://noaa-nmme-pds` are open.
* **IRI ENSO plume** — *no longer serves numeric data* (figure only since ~Sep 2026).
  Not a viable numeric dependency.

## Tropical cyclones

* **IBTrACS v04r01** (`WP` basin CSV/NetCDF) — multi-agency best tracks.
  **Implemented.** WMO wind/pressure = responsible agency (JMA 10-min for WP);
  per-agency `USA_WIND`/`TOKYO_WIND` retained so averaging periods stay explicit.
* **JMA RSMC Tokyo** JSON (`targetTc.json`, `specifications.json`, `forecast.json`,
  `pastTracks.json`) — authoritative active-storm source. **Implemented.**
* **JTWC** text warnings (`tgftp.nws.noaa.gov/data/raw/wt/wtpn3x.pgtw..txt`) — 1-min
  wind + quadrant radii + forecast track. **Implemented** (full ATCF-text parser).
* **NWS Guam / PEAC** (`wtpq3x.pgum.*`, `api.weather.gov/alerts`) — FAS island-specific
  watches/warnings. **Implemented** (TCP parser `nws_guam.py`; `api.weather.gov/
  alerts` available for structured zone alerts).
* ⚠️ Wind-speed averaging differs by agency (JMA 10-min vs JTWC/NWS 1-min). Always
  carry the agency + averaging period with any wind value.

## Satellite imagery

* **Himawari-9** (JMA/NICT real-time web) — full-disk visible composite, 10-min
  cadence. **Implemented** (latest full-disk tile shown on the Tropical Cyclones
  page). IR bands and region-zoom tiles are a follow-up.
* **GOES** (NOAA) — *not a fit for the FAS*: GOES-West covers the eastern Pacific/
  Americas; the FAS (130–175E) is in Himawari's domain.
* **Sentinel-2/3** (Copernicus, free) and **VIIRS** (NASA/NOAA, Earthdata) — ocean/
  land remote sensing (SST, ocean colour, vegetation), not weather feeds; heavy
  raster. *Planned* for SST/coastal overlays (STAC/AWS/LANCE access documented).

## Precipitation & drought

* **CHIRPS v3** (`data.chc.ucsb.edu/products/CHIRPS/v3.0/`) — **implemented** (point
  extraction from monthly COGs via rasterio range requests). 0.05°, 60N–60S, CC BY 4.0.
  **Land-masked** → sub-pixel islands use a documented max-valid-pixel heuristic; ERA5
  is preferred for ocean-adjacent atolls.
* **NASA GPM IMERG** (GES DISC) — global incl. ocean, 0.1°, sub-daily.
  **Implemented & tested** (`earthaccess` adapter `ingestion/imerg.py` for daily
  point extraction; live-verified with an Earthdata bearer token). Requires
  `EARTHDATA_TOKEN` (or `.netrc`) + a one-time GPM IMERG EULA acceptance.
  Note V07→V08 transition (V07 Final ends Sep 2025).
* **PERSIANN-CDR** (NOAA NCEI) — 0.25° daily, 1983–present, no login.
* **GPCC** (DWD) — gauge-only land; essentially no FAS gauges → *not recommended*.
* **USGS P1RXUMV3** (western-Pacific drought + 7-day GFS forecast) — covers **FSM,
  RMI, Nauru, Solomon — Palau NOT included**. ScienceBase blocks non-browser GET.
  Reuse its R scripts to replicate the IMERG-Early-Run + GFS pipeline for Palau.
* **SPEIbase / SPEI monitor** — global land 0.5°/1° (ODbL); many FAS atolls fall
  between cells. Better to compute SPI/SPEI ourselves from CHIRPS/IMERG (SPI is
  already implemented in `drought/spi.py`).

## Population, boundaries, terrain, infrastructure

* **WorldPop** (`data.worldpop.org/.../Global_2000_2020_1km/`) — **implemented** (point/radius
  extraction via rasterio). CC BY 4.0, ~1 km, 2000–2020, covers PLW/FSM/MHL, no login.
  UN-adjusted 2020 totals exceed censuses → used for **spatial exposure**, not as the
  census of record. (WOPR does *not* cover these countries.)
* **GPWv4** (SEDAC) — ~1 km, requires Earthdata Login; census-consistent cross-check.
* **HDX COD-AB boundaries** — FSM (`cod-ab-fsm`) and RMI (`cod-ab-mhl`), CC BY-IGO,
  reviewed Oct 2024. **Implemented** (loaded via `pyshp` + `rasterio`, no GDAL/
  geopandas) — enables accurate zonal WorldPop population per atoll/state.
  **Palau** (no COD-AB) uses **geoBoundaries ADM1** (16 states, ODbL/OSM), parsed
  from GeoJSON — also implemented.
* **Copernicus DEM GLO-30/GLO-90** (AWS Open Data, no login) — DSM terrain.
* **GEBCO** (CC BY 4.0) — 15 arc-sec topography+bathymetry (atoll coastal exposure).
* **SRTM GL1** (30 m) — via OpenTopography S3 or Earthdata (login).
* **OSM / Geofabrik / HOT** (ODbL) — the only open infrastructure/POI layer; coverage
  is uneven (Koror/Majuro/Pohnpei well mapped, outer atolls thin).

## AI / global forecast models

* **Google WeatherNext 3** — allowlist-gated (free Google account, ~5–7 day approval),
  Zarr v3 / BigQuery / Earth Engine, 0.05°/0.1°/0.25°, hourly, 64-member, 15-day.
  Real-time data under an experimental ToU; historical (≥1 h old) is CC BY 4.0.
  **Adapter implemented** (`ingestion/weathernext.py`): reports `requires_credentials`
  and reads Zarr via `gcsfs` once the allowlist is granted. Access form submitted
  (see below).
* **NVIDIA Earth-2 / FourCastNet / StormCast** — open downloadable weights (NGC/HF,
  self-host on GPU via Modulus) or hosted NIM microservices (paid API key / DGX Cloud).
  **No keyless free hosted weather API.** Adapter implemented and reports honestly.
* **ECMWF AIFS open data** (`s3://ecmwf-forecasts`, CC BY 4.0, no account) — 0.25°,
  4×/day to 15 days, GRIB2. **Best free AI/global drop-in** (per-point via
  `ecmwf-opendata`).
* **NOAA GFS/GEFS** (NOMADS / AWS NODD `s3://noaa-gfs-bdp-pds`) — public domain,
  0.25°, byte-range GRIB2 subsetting. **Free fallback.**

### AI-model account status

* **WeatherNext 3**: the access form requires (1) a Google account email, (2) a
  Google Cloud account email to be allowlisted, (3) name/country/organisation. The
  approval is 5–7 business days at Google's discretion. **Not yet granted.**
* **NVIDIA**: a free `build.nvidia.com` key covers LLM/vision/embedding NIMs, **not**
  the weather microservices (those need DGX Cloud). Signing up would not unblock a
  hosted weather feed, so it is not pursued.

## Requested but not freely accessible

* **Windy** — commercial API only (`api.windy.com`); no free tier. Equivalent model
  data (ECMWF/GFS/ICON/GEM) is already integrated via Open-Meteo multi-model.
* **Weather Underground** — the free API was discontinued (2023); commercial only.
* **Meteoconsult** — no public free API, limited Pacific coverage.
* **NOAA US Drought Monitor (USDM)** — **US-only** (does not cover Palau/FSM/RMI).
  The app computes an internal precipitation-percentile **D0–D4** drought level
  instead, and uses CHIRPS/IMERG/ERA5 for drought indicators.

## Maps & basemaps

The original Plotly `scattergeo` map showed the FAS atolls as invisible dots on a
blank ocean. Replaced with interactive Leaflet (folium) maps using **keyless
satellite basemaps** so the islands are actually visible:

* **Esri World Imagery** — high-res commercial-satellite mosaic (zoom 19); default.
* **NASA GIBS** BlueMarble / MODIS Terra / MODIS Aqua / VIIRS — official NASA EOSDIS
  daily true-colour (~250 m), no key. Tile-matrix-set names are layer-specific
  (`GoogleMapsCompatible_Level8/9`).
* **OpenStreetMap** — street fallback.

Basemaps are chosen client-side via a Leaflet layer control; tiles load in the
browser directly from GIBS/Esri (no server-side proxy, no credentials).

## Attribution & license notes

Open-Meteo (CC BY 4.0), ERA5 (CC BY 4.0 via CDS), CHIRPS v3 (CC BY 4.0), WorldPop
(CC BY 4.0), GPWv4 (CC BY 4.0), GEBCO (CC BY 4.0), AIFS (CC BY 4.0). NOAA/NCEP/NCEI,
USGS, NASA, JTWC, NWS, JMA observational data are public-domain/observational.
SPEIbase is ODbL 1.0; HDX COD-AB is CC BY-IGO; OSM/Geofabrik/HOT are ODbL.
WeatherNext 3 real-time data is under a restrictive experimental ToU (historical is
CC BY 4.0). Always confirm each source's terms before redistribution.
