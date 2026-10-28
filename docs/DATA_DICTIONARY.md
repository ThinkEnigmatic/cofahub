# Data Dictionary

## Geography registry (`config/geography.yaml`)

| Field | Type | Description |
| --- | --- | --- |
| geo_id | str | Stable identifier (e.g. `PAL`, `FSM-CHUUK`, `RMI-MAJ`). |
| name | str | Display name. |
| entity_type | str | `country`, `state`, `island`, `atoll`, `monitoring_location`. |
| country_code | str | ISO-3166 alpha-2 (PW / FM / MH). |
| parent_geo_id | str | Parent entity id (null for countries). |
| latitude / longitude | float | Approximate point location (seed, not surveyed). |
| area_km2 | float | Approximate area (seed). |
| population / population_year | int | Approximate population (seed). |
| population_source | str | Provenance of the population figure. |
| data_coverage | str | Qualitative coverage (moderate / sparse). |
| notes | str | Caveats. |

> The registry is **seed data** (`status: seed`). A validated FAS island/atoll
> inventory can replace it without code changes.

## Weather forecast (`open-meteo-forecast`)

Hourly/daily DataFrames; metric units (°C, mm, m/s, hPa, %). Key columns:
`temperature_2m`, `precipitation`, `relative_humidity_2m`, `wind_speed_10m`,
`wind_direction_10m`, `surface_pressure`, `precipitation_sum` (daily),
`precipitation_probability_max` (daily). Metadata includes `latitude`,
`longitude`, `elevation_m`, `timezone`, and attribution note.

## Historical rainfall (`open-meteo-archive`)

Daily `precip_mm` Series (mm), tz-aware UTC, with NaN for missing days.

## Derived indicators

| Field | Description |
| --- | --- |
| `rain_{n}m_mm` | Rolling n-month rainfall total (n ∈ 1,3,6,12); NaN if any month incomplete. |
| `anomaly_mm` | Monthly total − calendar-month climatology (baseline-valid only). |
| `anomaly_pct` | (obs − clim) / clim × 100. |
| `percentile` | Empirical percentile of the month vs its calendar-month baseline distribution. |
| `percentile_category` | Severity label from percentile bins (config). |

## Provenance record

Every derived value records: `dataset_id`, `source_url`, `retrieved_at`,
`valid_time`, `init_time`, `lead_time`, `calculation_method`, `parameters`,
`baseline_period`, `geographic_aggregation`, `missing_data_handling`,
`output_timestamp`, `code_version`, `notes`.
