"""Timestamp normalization and timezone handling.

All internal timestamps are stored as timezone-aware UTC. This module provides
predictable normalization so that naive/aware, ISO/epoch, and pandas inputs all
reduce to the same canonical form.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd


def normalize_timestamp(value) -> pd.Timestamp:
    """Normalize a datetime-like value to a tz-aware UTC ``pandas.Timestamp``.

    Accepts ISO-8601 strings, ``datetime`` (naive or aware), ``date``, numeric
    epoch seconds, and pandas timestamps. Naive datetimes are assumed UTC.

    Raises
    ------
    ValueError
        If the value cannot be interpreted as a timestamp.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("Cannot normalize a null timestamp")

    if isinstance(value, pd.Timestamp):
        ts = value
    elif isinstance(value, datetime):
        ts = pd.Timestamp(value)
    elif isinstance(value, (int, float)):
        # numeric epoch (seconds since 1970-01-01 UTC)
        ts = pd.Timestamp(datetime.fromtimestamp(value, tz=UTC))
    else:
        ts = pd.to_datetime(value, utc=False, errors="raise")

    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    return ts


def format_iso(value) -> str:
    """Format a timestamp as a compact ISO-8601 UTC string."""
    return normalize_timestamp(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def as_utc_naive(value) -> pd.Timestamp:
    """Return a tz-naive UTC timestamp (for storage in naive columns)."""
    ts = normalize_timestamp(value)
    return ts.tz_localize(None)


def now_utc() -> pd.Timestamp:
    """Return the current time as tz-aware UTC."""
    return pd.Timestamp.now(tz=UTC)


def localize(value, tz_name: str) -> pd.Timestamp:
    """Convert a timestamp to a named IANA timezone (e.g. "Pacific/Chuuk")."""
    return normalize_timestamp(value).tz_convert(tz_name)
