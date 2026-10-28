# Data Sources

Status values: `implemented_and_tested`, `implemented_but_not_verified`,
`requires_credentials`, `requires_manual_import`, `planned`, `unavailable`.
A source is marked `implemented_and_tested` only after a successful integration
test.

| Source | Publisher | URL | Status | Verified |
| --- | --- | --- | --- | --- |
| Open-Meteo Forecast API | Open-Meteo | https://open-meteo.com/ | ✅ implemented_and_tested | 2026-10-28 |
| Open-Meteo Historical Weather (ERA5) | Open-Meteo / ECMWF | https://open-meteo.com/en/docs/historical-weather-api | ✅ implemented_and_tested | 2026-10-28 |
| NOAA CPC ENSO (ONI / Diagnostic Discussion) | NOAA CPC | https://www.cpc.ncep.noaa.gov/ | 🗓️ planned | — |
| IBTrACS (best tracks) | NOAA/NCEI | https://www.ncei.noaa.gov/products/international-best-track-archive | 🗓️ planned | — |
| NASA GPM IMERG | NASA | https://gpm.nasa.gov/data/imerg | 🗓️ planned (needs Earthdata login) | — |
| Google WeatherNext 3 | Google | https://developers.google.com/weathernext/guides/access-forecast | 🚫 unavailable (needs approval) | — |
| USGS Western Pacific drought (DOI 10.5066/P1RXUMV3) | USGS | https://doi.org/10.5066/P1RXUMV3 | 🗓️ planned (coverage unverified) | — |
| WorldPop population | WorldPop | https://www.worldpop.org/ | 🗓️ planned | — |

## Verified integrations

### Open-Meteo Forecast (`implemented_and_tested`)
* **Endpoint:** `https://api.open-meteo.com/v1/forecast` (no key; free tier).
* **Variables:** temperature_2m, relative_humidity_2m, precipitation, weather_code,
  wind_speed_10m, wind_direction_10m, surface_pressure (current + hourly + daily).
* **Horizon:** up to 16 days; **resolution:** ~11 km model grid.
* **License:** data CC BY 4.0 (attribution required).
* **Verified:** live `test_network.py::test_live_forecast` and
  `scripts/ingest_weather.py` (Koror current conditions fetched and validated).

### Open-Meteo Historical Weather / ERA5 (`implemented_and_tested`)
* **Endpoint:** `https://archive-api.open-meteo.com/v1/archive`.
* **Variables:** daily precipitation_sum (basis for climatology/anomalies).
* **Resolution:** ~25 km ERA5 reanalysis (coarser than the forecast grid).
* **Verified:** live `test_network.py::test_live_archive_rainfall`.

## Not yet wired in (planned)

* **NOAA CPC ONI** — authoritative ENSO classification. Until implemented, the
  app reports ENSO status as *unavailable* (no phase is assumed). Target:
  `https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt`.
* **IBTrACS** — historical tropical cyclone tracks (Phase 5). Sample tracks are
  used until then.
* **Official advisories / watches / warnings** — no source is wired in; none are
  fabricated.
* **IMERG, WorldPop, USGS drought, WeatherNext 3** — see ROADMAP.

## Attribution & license notes

Open-Meteo data is CC BY 4.0 (attribution). NOAA/NCEI/USGS/NASA products are U.S.
Government public domain (verify per product). Reanalysis (ERA5) is CC BY 4.0 via
the Copernicus Climate Data Store. WeatherNext 3 requires access approval and is
not accessible by default.
