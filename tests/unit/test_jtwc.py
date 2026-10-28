"""JTWC warning parser tests."""

from __future__ import annotations

from cofa_forward.ingestion.jtwc import JtwcAdapter, parse_jtwc_warning

_SAMPLE = """WTPN31 PGTW 270300
MSGID/GENADMIN/JOINT TYPHOON WRNCEN PEARL HARBOR HI//
SUBJ/TYPHOON 30W (IN-FA) WARNING NR 015//
RMKS/
1. TYPHOON 30W (IN-FA) WARNING NR 015    
   01 ACTIVE TROPICAL CYCLONE IN NORTHWESTPAC
   MAX SUSTAINED WINDS BASED ON ONE-MINUTE AVERAGE
   WIND RADII VALID OVER OPEN WATER ONLY
    ---
   WARNING POSITION:
   270000Z --- NEAR 14.3N 162.4E
     MOVEMENT PAST SIX HOURS - 295 DEGREES AT 02 KTS
   PRESENT WIND DISTRIBUTION:
   MAX SUSTAINED WINDS - 110 KT, GUSTS 135 KT
   RADIUS OF 064 KT WINDS - 025 NM NORTHEAST QUADRANT
                            030 NM NORTHWEST QUADRANT
   RADIUS OF 034 KT WINDS - 080 NM NORTHEAST QUADRANT
   REPEAT POSIT: 14.3N 162.4E
    ---
   FORECASTS:
   12 HRS, VALID AT:
   271200Z --- 14.5N 161.5E
   MAX SUSTAINED WINDS - 110 KT, GUSTS 135 KT
   VECTOR TO 24 HR POSIT: 280 DEG/ 07 KTS
    ---
   24 HRS, VALID AT:
   280000Z --- 14.7N 160.0E
   MAX SUSTAINED WINDS - 120 KT, GUSTS 145 KT
"""


def test_parse_jtwc_header_and_identity():
    p = parse_jtwc_warning(_SAMPLE)
    assert p["header"] == "WTPN31"
    assert p["agency"] == "PGTW"
    assert p["storm_id"] == "30W"
    assert p["name"] == "IN-FA"
    assert p["warning_number"] == "015"


def test_parse_jtwc_position_and_wind():
    p = parse_jtwc_warning(_SAMPLE)
    assert p["position"] == {"lat": 14.3, "lon": 162.4}
    assert p["wind_kt"] == 110
    assert p["gusts_kt"] == 135
    assert p["movement_dir_deg"] == 295
    assert p["movement_speed_kt"] == 2


def test_parse_jtwc_radii():
    p = parse_jtwc_warning(_SAMPLE)
    assert p["wind_radii_nm"][64]["NE"] == 25
    assert p["wind_radii_nm"][64]["NW"] == 30
    assert p["wind_radii_nm"][34]["NE"] == 80


def test_parse_jtwc_forecasts():
    p = parse_jtwc_warning(_SAMPLE)
    assert len(p["forecasts"]) == 2
    fc0 = p["forecasts"][0]
    assert fc0["hours"] == 12
    assert fc0["position"] == {"lat": 14.5, "lon": 161.5}
    assert fc0["wind_kt"] == 110
    assert p["forecasts"][1]["hours"] == 24


def test_jtwc_adapter_marks_1min():
    a = JtwcAdapter()
    assert a.source_id == "jtwc-advisories"
