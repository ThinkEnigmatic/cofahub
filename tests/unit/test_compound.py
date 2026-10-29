"""Compound-hazard flag tests."""

from __future__ import annotations

from cofa_forward.hazards.compound import compound_flags


def test_no_flags_when_conditions_benign():
    flags = compound_flags(drought_quintile="Typical", peac_index="Dark Green", wave_height_m=1.0)
    assert flags == []


def test_drought_and_large_seas_flag():
    flags = compound_flags(drought_quintile="Dry", peac_index="Yellow", wave_height_m=3.0)
    assert any("Drought + large seas" in f for f in flags)


def test_peac_red_and_large_seas():
    flags = compound_flags(drought_quintile="Typical", peac_index="Red", wave_height_m=3.0)
    assert any("PEAC Red" in f for f in flags)


def test_drought_and_cyclone():
    flags = compound_flags(
        drought_quintile="Drier",
        peac_index="Yellow",
        wave_height_m=1.0,
        cyclone_km=120.0,
        cyclone_name="Test",
    )
    assert any("tropical cyclone" in f and "Test" in f for f in flags)
    # Cyclone far away -> no flag.
    flags2 = compound_flags(
        drought_quintile="Drier",
        peac_index="Yellow",
        wave_height_m=1.0,
        cyclone_km=500.0,
    )
    assert not any("tropical cyclone" in f for f in flags2)


def test_high_waves_without_drought_no_flag():
    flags = compound_flags(drought_quintile="Wetter", peac_index="Dark Green", wave_height_m=4.0)
    assert flags == []
