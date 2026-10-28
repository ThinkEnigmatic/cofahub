# Validation & Verification

## Test suite

```bash
uv run pytest              # offline suite (unit + integration + regression)
uv run pytest -m network   # live provider tests (requires internet)
uv run ruff check .        # lint
uv run ruff format --check .  # format
uv run python scripts/verify_pages.py  # render every page via AppTest
```

Current: **87 offline tests pass, 2 live network tests pass** (Open-Meteo
forecast + archive), all 9 pages render without exceptions, lint clean.

## Scientific regression tests

Small version-controlled synthetic datasets verify known results:

* a known rainfall sequence produces expected rolling totals;
* a known baseline produces expected anomaly and percentile;
* a known track produces expected distances to a test location;
* a known ENSO event catalog returns the expected matching episode;
* missing months never become zero rainfall;
* an incomplete climatological baseline is rejected/flagged;
* a report never claims current conditions from stale data (ENSO status is
  "unavailable" until a source is wired in).

## Forecast verification framework

A verification module (bias, MAE, RMSE vs a climatological baseline) is **not yet
implemented** — it is a documented next step that requires time-matched forecast
and observation archives. The hooks for it are the same provenance framework used
elsewhere.

## Known limitations

* ENSO current state is **unavailable** (no CPC ONI source wired in).
* Percentile/anomaly indicators run on **synthetic sample** series until ERA5
  archive data is pulled per location.
* Geography is **point-based seed data**, not validated boundaries.
* No official advisories, IBTrACS, or exposure overlays yet.
