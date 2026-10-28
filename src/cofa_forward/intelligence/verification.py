"""Forecast verification framework.

Computes bias, MAE, RMSE, and a climatological skill score from time-matched
forecast/observation pairs. Only time-matched values are compared; mismatched or
incompatible time periods are never silently evaluated.
"""

from __future__ import annotations

import pandas as pd


def align(observed: pd.Series, forecast: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Return time-matched observed/forecast series (inner join on index)."""
    common = observed.index.intersection(forecast.index)
    return observed.loc[common], forecast.loc[common]


def bias(observed: pd.Series, forecast: pd.Series) -> float:
    """Mean error (forecast − observed)."""
    o, f = align(observed, forecast)
    return float((f - o).mean())


def mae(observed: pd.Series, forecast: pd.Series) -> float:
    """Mean absolute error."""
    o, f = align(observed, forecast)
    return float((f - o).abs().mean())


def rmse(observed: pd.Series, forecast: pd.Series) -> float:
    """Root mean squared error."""
    o, f = align(observed, forecast)
    return float(((f - o) ** 2).mean() ** 0.5)


def pearson(observed: pd.Series, forecast: pd.Series) -> float:
    """Pearson correlation between matched forecast and observed."""
    o, f = align(observed, forecast)
    if len(o) < 2:
        return float("nan")
    return float(o.corr(f))


def _climatology_reference(observed: pd.Series, climatology: pd.Series | float) -> pd.Series:
    if isinstance(climatology, (int, float)):
        return pd.Series(float(climatology), index=observed.index)
    common = observed.index.intersection(climatology.index)
    return climatology.loc[common]


def climatology_rmse(observed: pd.Series, climatology: pd.Series | float) -> float:
    """RMSE of a climatological (persistence) baseline against observations."""
    ref = _climatology_reference(observed, climatology)
    if len(ref) == 0:
        return float("nan")
    return float(((observed.loc[ref.index] - ref) ** 2).mean() ** 0.5)


def verify(
    observed: pd.Series,
    forecast: pd.Series,
    climatology: pd.Series | float | None = None,
) -> dict:
    """Verify a forecast against observations.

    Returns a dict with n, mean_obs, mean_fcst, bias, mae, rmse, pearson, and —
    if ``climatology`` is provided — ``rmse_climatology`` and ``skill_score``
    (1 − RMSE_fcst / RMSE_clim; positive means better than climatology).
    """
    o, f = align(observed, forecast)
    n = int(len(o))
    if n == 0:
        return {
            "n": 0,
            "bias": float("nan"),
            "mae": float("nan"),
            "rmse": float("nan"),
            "pearson": float("nan"),
            "mean_obs": float("nan"),
            "mean_fcst": float("nan"),
            "note": "no time-matched observations",
        }

    out = {
        "n": n,
        "bias": bias(o, f),
        "mae": mae(o, f),
        "rmse": rmse(o, f),
        "pearson": pearson(o, f),
        "mean_obs": float(o.mean()),
        "mean_fcst": float(f.mean()),
    }
    if climatology is not None:
        rmse_clim = climatology_rmse(observed, climatology)
        out["rmse_climatology"] = rmse_clim
        if rmse_clim not in (0.0, float("nan")) and rmse_clim == rmse_clim:
            out["skill_score"] = 1.0 - out["rmse"] / rmse_clim
        else:
            out["skill_score"] = float("nan")
    return out
