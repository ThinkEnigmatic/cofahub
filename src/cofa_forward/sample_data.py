"""Deterministic synthetic sample data (clearly labeled).

Synthetic data exists so the app is usable offline and tests are reproducible.
It is ALWAYS labeled as sample data in the UI and never confused with live data.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd


def _stable_seed(*parts) -> int:
    """Deterministic, process-stable integer seed from arbitrary values."""
    h = hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


# Approximate monthly mean rainfall (mm/month) for a representative tropical
# western-Pacific climate. This is a plausible shape, NOT a measured climatology.
_SYNTH_MONTHLY_MM = np.array(
    [220, 180, 180, 220, 320, 380, 400, 380, 330, 330, 300, 280], dtype=float
)


def synthetic_daily_rainfall(
    geo_id: str,
    years: int = 30,
    seed: int = 0,
    end: str = "2026-10-28",
) -> pd.Series:
    """Deterministic synthetic daily rainfall (mm) for a location.

    Uses a fixed monthly climatology plus multiplicative log-normal noise, seeded
    by (geo_id, seed). Output is a tz-naive UTC daily series ending at ``end``.
    """
    rng = np.random.default_rng(_stable_seed(geo_id, seed))
    end_ts = pd.Timestamp(end)
    start_ts = end_ts - pd.Timedelta(days=365 * years)
    idx = pd.date_range(start_ts, end_ts, freq="D")
    monthly = np.array([_SYNTH_MONTHLY_MM[d.month - 1] for d in idx])
    days_in_month = np.array([d.days_in_month for d in idx])
    daily_mean = monthly / days_in_month
    noise = rng.lognormal(mean=0.0, sigma=0.9, size=len(idx))
    # dry-day structure: ~20% of days are dry, scaled by a rainy-season factor
    dry_mask = rng.random(len(idx)) < 0.22
    precip = daily_mean * noise
    precip[dry_mask] = 0.0
    return pd.Series(precip, index=idx, name="precip_mm").round(2)


def synthetic_forecast(
    geo_id: str,
    lat: float,
    lon: float,
    seed: int = 0,
    hours: int = 48,
) -> pd.DataFrame:
    """Deterministic synthetic hourly forecast for a location (clearly labeled)."""
    rng = np.random.default_rng(_stable_seed(geo_id, "fc", seed))
    now = pd.Timestamp.utcnow().floor("h")
    idx = pd.date_range(now, periods=hours, freq="h")
    t = np.arange(hours)
    diurnal = np.sin((t - 6) / 24 * 2 * np.pi) * 3.0  # diurnal temperature swing
    temp = 27.5 + diurnal + rng.normal(0, 0.5, hours)
    rain = np.where(rng.random(hours) < 0.18, rng.exponential(4.0, hours), 0.0)
    wind = 5.0 + rng.weibull(1.8, hours) * 3.0
    wind_dir = (rng.uniform(0, 360, hours)).round(0)
    hum = 80.0 + rng.normal(0, 4, hours)
    pressure = 1010.0 + rng.normal(0, 1.2, hours)
    df = pd.DataFrame(
        {
            "time": idx,
            "temperature_2m_c": temp.round(1),
            "precipitation_mm": rain.round(1),
            "wind_speed_10m_ms": wind.round(1),
            "wind_direction_deg": wind_dir,
            "relative_humidity_2m_pct": hum.round(0),
            "surface_pressure_hpa": pressure.round(1),
        }
    )
    df["geo_id"] = geo_id
    df["label"] = "sample"
    return df


def synthetic_tracks(seed: int = 0) -> pd.DataFrame:
    """A small synthetic tropical cyclone track set (clearly labeled, NOT real storms)."""
    rng = np.random.default_rng(seed)
    storms = []
    for s in range(3):
        sid = f"SAMPLE-{s + 1:02d}"
        n = 12
        lat = 5.0 + np.cumsum(rng.uniform(-0.4, 0.6, n))
        lon = 138.0 + np.cumsum(rng.uniform(0.8, 1.6, n))
        base = pd.Timestamp("2025-08-01") + pd.Timedelta(days=s * 14)
        times = [base + pd.Timedelta(hours=6 * i) for i in range(n)]
        wind = np.clip(25 + np.arange(n) * 6 + rng.normal(0, 3, n), 20, 120).round(0)
        pressure = np.clip(1005 - (wind - 25) * 0.5, 900, 1005).round(0)
        for i in range(n):
            storms.append(
                {
                    "storm_id": sid,
                    "time": times[i],
                    "lat": round(float(lat[i]), 2),
                    "lon": round(float(lon[i]), 2),
                    "wind_kt": float(wind[i]),
                    "pressure_hpa": float(pressure[i]),
                    "agency": "SAMPLE",
                }
            )
    df = pd.DataFrame(storms)
    df["label"] = "sample"
    return df


def synthetic_impacts(seed: int = 0) -> pd.DataFrame:
    """A clearly-labeled synthetic historical impact catalog (NOT real impacts)."""
    records = [
        {
            "event_id": "SAMPLE-DROUGHT-2016",
            "event_name": "Sample drought episode (illustrative)",
            "hazard_type": "drought",
            "start_date": "2015-12-01",
            "end_date": "2016-04-30",
            "country": "Palau",
            "geo_id": "PAL",
            "enso_phase": "el_nino",
            "enso_episode_id": "2015-16",
            "observed_conditions": "Illustrative below-normal rainfall (synthetic)",
            "reported_impacts": "Illustrative freshwater stress (synthetic)",
            "affected_population": None,
            "evidence_quality": "sample",
            "confidence": "sample",
            "verification_status": "sample",
        },
        {
            "event_id": "SAMPLE-STORM-1997",
            "event_name": "Sample tropical cyclone (illustrative)",
            "hazard_type": "tropical_cyclone",
            "start_date": "1997-11-01",
            "end_date": "1997-11-04",
            "country": "FSM",
            "geo_id": "FSM-CHUUK",
            "enso_phase": "el_nino",
            "enso_episode_id": "1997-98",
            "observed_conditions": "Illustrative near-passing storm (synthetic)",
            "reported_impacts": "Illustrative wind/rain impacts (synthetic)",
            "affected_population": None,
            "evidence_quality": "sample",
            "confidence": "sample",
            "verification_status": "sample",
        },
    ]
    return pd.DataFrame(records)
