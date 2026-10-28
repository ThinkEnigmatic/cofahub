# Validation & Verification

## Test suite

```bash
uv run pytest              # offline suite (unit + integration + regression)
uv run pytest -m network   # live provider tests (requires internet)
uv run ruff check .        # lint
uv run ruff format --check .  # format
uv run python scripts/verify_pages.py  # render every page via AppTest
```

Current: **122 offline tests pass, 5 live network tests pass** (Open-Meteo
forecast + archive, CPC ONI, JMA RSMC Tokyo, IBTrACS), all 9 pages render
without exceptions, lint clean.

## Scientific regression tests

Small version-controlled synthetic datasets verify known results:

* a known rainfall sequence produces expected rolling totals;
* a known baseline produces expected anomaly and percentile;
* a known track produces expected distances to a test location;
* a known ENSO event catalog returns the expected matching episode;
* missing months never become zero rainfall;
* an incomplete climatological baseline is rejected/flagged;
* a report never claims current conditions from stale data (ENSO phase is derived
  from the live ONI and clearly labeled as derived, never inferred from an old
  report).

## Forecast verification framework

A verification module (`intelligence/verification.py`) computes bias, MAE, RMSE,
Pearson correlation, and a climatological skill score on time-matched
forecast/observation pairs. It is implemented and unit-tested; applying it to real
forecast-vs-archive comparisons is a follow-up that requires time-matched archives.

## Known limitations

* ENSO **current state is live** (CPC ONI); the official *status statement*
  (Diagnostic Discussion) is not yet scraped.
* Percentile/anomaly indicators run on **synthetic sample** series until real
  CHIRPS/IMERG/ERA5 rainfall is pulled per location (the ERA5 path already works
  via `scripts/ingest_rainfall.py`).
* Geography is **point-based seed data**, not validated boundaries (HDX COD-AB /
  SPC are the researched sources for polygons).
* JTWC text warnings and NWS Guam advisories are **planned, not yet wired**; the
  JMA active-storm + IBTrACS historical-track adapters are live.
* No exposure overlays (WorldPop/GEBCO) integrated yet.
