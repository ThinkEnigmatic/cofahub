"""ENSO analog selection tests."""

from __future__ import annotations

import pandas as pd

from cofa_forward.climate.enso_analog import enso_analogs, episode_peak_oni
from cofa_forward.schemas import EnsoEpisode


def _oni() -> pd.DataFrame:
    # 1997-98 (peak ~2.4) and 2015-16 (peak ~2.6) and 2009-10 (peak ~1.6).
    idx = pd.date_range("1997-01-01", periods=240, freq="MS")
    anom = [0.2] * len(idx)
    for i, d in enumerate(idx):
        if pd.Timestamp("1997-10-01") <= d <= pd.Timestamp("1998-02-01"):
            anom[i] = 2.4
        if pd.Timestamp("2009-11-01") <= d <= pd.Timestamp("2010-01-01"):
            anom[i] = 1.6
        if pd.Timestamp("2015-11-01") <= d <= pd.Timestamp("2016-01-01"):
            anom[i] = 2.6
    return pd.DataFrame({"date": idx, "anom": anom})


def _episodes():
    return [
        EnsoEpisode(
            id="1997-98",
            phase="el_nino",
            start="1997-05-01",
            end="1998-05-31",
            intensity="very_strong",
        ),
        EnsoEpisode(
            id="2009-10",
            phase="el_nino",
            start="2009-06-01",
            end="2010-04-30",
            intensity="moderate",
        ),
        EnsoEpisode(
            id="2015-16",
            phase="el_nino",
            start="2015-03-01",
            end="2016-05-31",
            intensity="very_strong",
        ),
        EnsoEpisode(
            id="2010-11",
            phase="la_nina",
            start="2010-06-01",
            end="2011-05-31",
            intensity="strong",
        ),
    ]


def test_episode_peak_oni():
    eps = _episodes()
    oni = _oni()
    assert episode_peak_oni(eps[0], oni) == 2.4  # 1997-98
    assert episode_peak_oni(eps[1], oni) == 1.6  # 2009-10


def test_enso_analogs_rank_closest_peak():
    eps = _episodes()
    oni = _oni()
    # Current ONI 2.6 -> 2015-16 (peak 2.6) first, then 1997-98 (2.4).
    top = enso_analogs("el_nino", 2.6, eps, oni)
    assert top[0]["episode_id"] == "2015-16"
    assert top[1]["episode_id"] == "1997-98"
    assert top[0]["similarity"] >= top[1]["similarity"]


def test_enso_analogs_only_same_phase():
    eps = _episodes()
    oni = _oni()
    top = enso_analogs("la_nina", 1.0, eps, oni)
    assert all(e["episode_id"] == "2010-11" for e in top)  # only the la_nina episode
