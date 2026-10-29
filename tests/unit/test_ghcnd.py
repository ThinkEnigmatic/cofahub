"""GHCNd adapter tests (offline, synthetic CSV)."""

from __future__ import annotations

import pandas as pd

from cofa_forward.ingestion.ghcnd import FAS_STATIONS, GhcndAdapter, parse_ghcnd


def _csv(rows: list[tuple]) -> str:
    header = (
        '"STATION","DATE","PRCP","PRCP_ATTRIBUTES",'
        '"TMAX","TMAX_ATTRIBUTES","TMIN","TMIN_ATTRIBUTES"'
    )
    lines = [header]
    for d, prcp, pflag, tmax, tmin in rows:
        lines.append(f'"RMW00040710","{d}",{prcp},"{pflag}",{tmax},",,0",{tmin},",,0"')
    return "\n".join(lines)


def test_parse_ghcnd_units_and_qa():
    # PRCP in tenths of mm, TMAX/TMIN in tenths of C; QA flag drops one value.
    raw = _csv(
        [
            ("2020-01-01", "100", ",,0", "300", "260"),  # 10.0 mm, 30.0C, 26.0C
            ("2020-01-02", "0", ",,0", "310", "265"),  # 0 mm
            ("2020-01-03", "9999", ",D", "300", "260"),  # QA-flagged -> dropped
            ("2020-01-04", "8000", ",,0", "300", "260"),  # 800 mm > 500 cap -> dropped
        ]
    )
    df = parse_ghcnd(raw)
    assert df["prcp_mm"].notna().sum() == 2  # only the two clean days
    assert df["prcp_mm"].iloc[0] == 10.0  # tenths -> mm
    assert df["tmax_c"].iloc[0] == 30.0  # tenths -> C
    assert df["tmin_c"].iloc[0] == 26.0
    # QA-flagged + over-cap days are NaN.
    assert pd.isna(df["prcp_mm"].iloc[2])
    assert pd.isna(df["prcp_mm"].iloc[3])


def test_parse_ghcnd_index_is_datetime():
    df = parse_ghcnd(_csv([("2020-01-01", "100", ",,0", "300", "260")]))
    assert isinstance(df.index, pd.DatetimeIndex)


def test_fas_stations_mapping():
    assert "RMI-MAJ" in FAS_STATIONS
    assert "PAL-KOR" in FAS_STATIONS
    assert "FSM-CHUUK" in FAS_STATIONS
    assert len(FAS_STATIONS) == 7
    # Each maps geo_id -> (station_id, wmo)
    sid, wmo = FAS_STATIONS["RMI-MAJ"]
    assert sid == "RMW00040710" and wmo == "91376"


def test_adapter_id():
    assert GhcndAdapter().source_id == "noaa-ghcnd"
