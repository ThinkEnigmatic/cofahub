"""ENSO Diagnostic Discussion + PERSIANN-CDR adapter tests (offline)."""

from __future__ import annotations

from cofa_forward.ingestion.enso_discussion import (
    CpcEnsoDiscussionAdapter,
    parse_enso_discussion,
)
from cofa_forward.ingestion.persiann_cdr import PersiannCdrAdapter, _file_url

_SAMPLE = """
<!DOCTYPE html><html><head><title>ENSO Diagnostic Discussion</title></head><body>
DIAGNOSTIC DISCUSSION<br>issued by CLIMATE PREDICTION CENTER/NCEP/NWS<br>
8 October 2026<br>
ENSO Alert System Status: <b>El Niño Advisory</b><br>
Synopsis: El Niño continues to strengthen, with a strong-to-very strong El Niño
likely through January-March 2027.<br>
In summary, El Niño continues to strengthen, with a strong-to-very strong El Niño
likely through January-March 2027.<br>
This discussion is a consolidated effort of NOAA.
</body></html>
"""


def test_parse_enso_discussion_extracts_fields():
    p = parse_enso_discussion(_SAMPLE)
    assert p["issue_date"] == "2026-10-08"
    assert p["alert_status"] == "El Niño Advisory"
    assert "strong-to-very strong" in p["synopsis"]
    assert "strong-to-very strong" in p["outlook_summary"]


def test_parse_enso_discussion_graceful_on_garbage():
    p = parse_enso_discussion("<html><body>nothing relevant</body></html>")
    assert p == {}


def test_enso_discussion_adapter_id():
    a = CpcEnsoDiscussionAdapter()
    assert a.source_id == "noaa-cpc-enso-discussion"


def test_persiann_file_url_shape():
    from datetime import date

    url = _file_url(date(2015, 1, 1))
    assert url.startswith("https://www.ncei.noaa.gov/data/precipitation-persiann/access/2015/")
    assert "PERSIANN-CDR_v01r01_20150101_c" in url


def test_persiann_adapter_id():
    a = PersiannCdrAdapter()
    assert a.source_id == "persiann-cdr"
