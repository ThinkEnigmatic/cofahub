"""CPC ONI adapter tests (offline parse + mocked fetch)."""

from __future__ import annotations

import pandas as pd

from cofa_forward.ingestion.base import FetchResult
from cofa_forward.ingestion.enso import CpcOniAdapter, classify_oni, parse_oni

_SAMPLE = """ SEAS  YR   TOTAL   ANOM
  JFM 2015  26.10   0.40
  FMA 2015  26.40   0.40
  MAM 2015  27.00   0.70
  AMJ 2015  27.50   1.00
  MJJ 2015  27.90   1.30
  JJA 2015  28.10   1.60
  JAS 2015  28.20   2.00
"""


def test_parse_oni():
    df = parse_oni(_SAMPLE)
    assert list(df.columns) == ["season", "year", "month", "total", "anom", "date"]
    assert len(df) == 7
    assert df.iloc[-1]["season"] == "JAS"
    assert df.iloc[-1]["year"] == 2015
    assert df.iloc[-1]["anom"] == 2.00
    assert str(df.iloc[-1]["date"].date()) == "2015-08-01"


def test_parse_oni_skips_header_and_garbage():
    df = parse_oni("SEAS YR TOTAL ANOM\n  JFM 2015 26.10 0.40\nbogus line\n")
    assert len(df) == 1


def test_classify_el_nino():
    df = pd.DataFrame({"anom": [0.6, 0.7, 0.8, 0.9, 1.0, 1.1]})
    assert classify_oni(df)["phase"] == "el_nino"


def test_classify_la_nina():
    df = pd.DataFrame({"anom": [-0.6, -0.7, -0.8, -0.9, -1.0]})
    assert classify_oni(df)["phase"] == "la_nina"


def test_classify_neutral():
    df = pd.DataFrame({"anom": [0.6, 0.2, -0.3, 0.1, 0.4]})
    assert classify_oni(df)["phase"] == "neutral"


def test_classify_empty():
    assert classify_oni(pd.DataFrame())["phase"] == "neutral"


def test_get_oni(monkeypatch):
    adapter = CpcOniAdapter()

    def fake_fetch(url, params=None, timeout=None):
        return FetchResult(True, "noaa-cpc-enso", url, data=_SAMPLE)

    monkeypatch.setattr(adapter, "fetch_text", fake_fetch)
    r = adapter.get_oni()
    assert r["ok"] is True
    assert r["latest"]["anom"] == 2.00
    assert r["phase"] == "el_nino"
    assert r["persistence_seasons"] == 5


def test_get_oni_failure(monkeypatch):
    adapter = CpcOniAdapter()

    def fake_fetch(url, params=None, timeout=None):
        return FetchResult(False, "noaa-cpc-enso", url, error="down")

    monkeypatch.setattr(adapter, "fetch_text", fake_fetch)
    r = adapter.get_oni()
    assert r["ok"] is False
    assert r["error"] == "down"
