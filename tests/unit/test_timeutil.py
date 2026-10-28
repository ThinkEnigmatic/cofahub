"""Timestamp normalization and timezone tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from cofa_forward.timeutil import format_iso, normalize_timestamp, now_utc


def test_normalize_naive_assumes_utc():
    ts = normalize_timestamp("2026-10-28T09:00:00")
    assert ts.tzinfo is not None
    assert ts.utcoffset().total_seconds() == 0
    assert ts.year == 2026 and ts.month == 10 and ts.day == 28


def test_normalize_aware_converts_to_utc():
    aware = datetime(2026, 10, 28, 9, 0, tzinfo=UTC)
    ts = normalize_timestamp(aware)
    assert str(ts.tzinfo) == "UTC"


def test_normalize_offset_timezone_converts():
    # +09:00 timezone (e.g. Palau) 09:00 -> 00:00 UTC
    import datetime as dt

    tz = dt.timezone(dt.timedelta(hours=9))
    aware = datetime(2026, 10, 28, 9, 0, tzinfo=tz)
    ts = normalize_timestamp(aware)
    assert ts.hour == 0


def test_normalize_epoch():
    ts = normalize_timestamp(0)
    assert ts.year == 1970 and ts.month == 1 and ts.day == 1


def test_normalize_pandas_timestamp():
    p = pd.Timestamp("2026-01-01")
    assert normalize_timestamp(p).year == 2026


def test_format_iso():
    assert format_iso("2026-10-28T09:00:00+00:00") == "2026-10-28T09:00:00Z"


def test_null_raises():
    with pytest.raises(ValueError):
        normalize_timestamp(None)


def test_now_utc_is_aware():
    assert now_utc().tzinfo is not None
