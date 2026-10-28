# Scientific Methods

## Rainfall accumulation

Daily rainfall is summed to monthly totals; a month is valid only if at least
80% of its days are present (`min_days_frac`). Incomplete months become NaN —
**never zero**. Rolling n-month totals require all n contributing months to be
valid; otherwise the total is NaN.

## Climatology & anomalies

* **Baseline:** 1991–2020 (configurable in `config/drought.yaml`).
* **Climatology:** mean rainfall per calendar month over the baseline.
* **Anomaly (mm):** observed − climatology. **Anomaly (%):** (obs − clim)/clim × 100.
* **Baseline validity:** an anomaly is computed only when ≥ `baseline_min_years`
  (default 15) years of valid data exist in the baseline; otherwise it is NaN and
  flagged.

## Percentile indicators

The empirical percentile of a month against its calendar-month baseline
distribution uses midpoint ranking: (count < value + 0.5 × count == value) / n.
Severity bins are configurable (`config/drought.yaml`). Percentile indicators are
implemented **before** SPI per the build plan.

## Standardized Precipitation Index (SPI)

`drought/spi.py` provides a non-parametric **normal-score transform**: the
empirical percentile mapped to a standard-normal quantile via the stdlib
`statistics.NormalDist`. It is a transparent approximation, **not** a full
gamma-fit SPI, and does not measure water availability directly. Full gamma-fit
SPI (with zero-precipitation and fitting handling) is a documented follow-up and
is disabled by default.

## Spatial attribution

* **Nearest-grid-cell** extraction (haversine, km) attributes model grid data to
  a registry point.
* This is **attribution of existing model data**, not downscaling. No output is
  labeled statistically or dynamically downscaled, because no downscaling is
  performed.
* A coarse grid cell over an atoll is never presented as atoll-accurate; the UI
  shows "regional model estimate; individual-atoll conditions may differ."

## Tropical cyclones

* **Distance** uses great-circle haversine (R = 6371.0088 km).
* **Proximity exposure** reports closest approach; it is **not** a wind-impact
  estimate (which needs storm size, intensity, and track uncertainty).
* **ENSO-conditioned analysis** reports counts with sample sizes and limitations;
  no causal claim is made from correlation and no hard-coded multiplier is turned
  into an operational risk probability.

## Historical analogs

Analogs are ranked by a weighted, normalized absolute-distance similarity over
ENSO phase/intensity and rainfall anomaly (see `climate/analogs.py`). Missing
features are excluded and reported. A historical analog is **contextual
evidence, not a forecast**.

## Confidence labels

Qualitative confidence is defined by criteria (see `intelligence/confidence.py`):
* **high** — sample ≥ 20 and good data quality (and high model agreement where
  applicable);
* **medium** — sample ≥ 8;
* **low** — small sample or limited quality;
* **unknown** — insufficient information.

No numerical confidence values are manufactured.

## Freshwater vulnerability

Meteorological drought, hydrological stress, reported shortage, and modeled
future risk are separate concepts. A composite score is not computed unless all
required inputs exist; otherwise meteorological indicators are shown and missing
inputs are listed explicitly.

## Water-need forecast (modeled water balance)

A deterministic water-balance model estimates, per island/atoll, whether forecast
rainfall over the next N days meets the population's water demand:

* daily demand (L) = population × `per_capita_lpd`
* catchment area (m²) = population × `per_person_catchment_m2`
* daily supply (L) = forecast precip (mm) × catchment (m²) × efficiency
  (1 mm over 1 m² = 1 L)
* required rainfall (mm) = total demand / (catchment × efficiency)
* balance (mm) = forecast rainfall − required rainfall (negative → projected deficit)

Defaults (`config/drought.yaml → freshwater.water_balance`): 100 L/person/day,
10 m²/person catchment, 0.8 collection efficiency, storage assumed 0
(conservative). These are **documented planning defaults, not measured site
data**; actual catchment, storage, desalination, and abstraction data are listed
as missing. The output is a **modeled rainfall-driven deficit/surplus**, never a
claim of actual water shortage.

## Bulletin monitoring

Authoritative sources that publish regular public bulletins (rather than stable
APIs) are polled by `ingestion/bulletins.py`: content is fetched, hashed, and —
on change — parsed into a structured summary, snapshotted to `data/raw/bulletins/`,
and logged as an update. Parsers cover NWS/JTWC WMO text products (header, agency,
issue time, headline), JMA typhoon bulletins, and the CPC ENSO Diagnostic
Discussion (the official ENSO alert status). See `docs/DATA_SOURCES.md`.
