"""Parquet read/write helpers for tabular and time-series data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def write_parquet(df: pd.DataFrame, path: Path | str, **kwargs: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, **kwargs)
    return path


def read_parquet(path: Path | str, **kwargs: Any) -> pd.DataFrame:
    return pd.read_parquet(path, **kwargs)
