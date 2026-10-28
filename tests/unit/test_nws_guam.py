"""NWS Guam advisory parser tests."""

from __future__ import annotations

from cofa_forward.ingestion.nws_guam import NwsGuamAdapter, parse_nws_guam_tcp

_SAMPLE = """WTPQ31 PGUM 281309
TCPPQ1

BULLETIN
Super Typhoon In-fa (30W) Intermediate Advisory Number 20A
National Weather Service Tiyan GU WP302026
1109 PM ChST Wed Oct 28 2026

...SUPER TYPHOON IN-FA STILL MOVING JUST NORTH OF WEST...

CHANGES WITH THIS ADVISORY
--------------------------

WATCHES AND WARNINGS
--------------------
A Typhoon Watch remains in effect for Alamagan, Pagan, and
Agrihan. A Typhoon Watch means that typhoon conditions, including
SUMMARY OF 1000 PM CHST...1200 UTC...INFORMATION
At 1000 PM CHST...1200 UTC...the center of Super Typhoon In-fa was
located near latitude 15.0 north...longitude 159.0 east.
"""


def test_parse_nws_guam_header_and_storm():
    p = parse_nws_guam_tcp(_SAMPLE)
    assert p["header"] == "WTPQ31"
    assert p["agency"] == "PGUM"
    assert p["storm_type"] == "Super Typhoon"
    assert p["name"] == "In-fa"
    assert p["storm_id"] == "30W"
    assert p["advisory_number"] == "20A"


def test_parse_nws_guam_watches_warnings():
    p = parse_nws_guam_tcp(_SAMPLE)
    assert any("Typhoon Watch" in w for w in p["watches_warnings"])


def test_nws_guam_adapter_id():
    a = NwsGuamAdapter()
    assert a.source_id == "nws-guam"
