"""USDm OCONUS shapefile parser + name-mapping tests."""

from __future__ import annotations

import io
import struct
import zipfile

from cofa_forward.ingestion.usdm import USDM_NAME_TO_GEO, _read_dbf, parse_oconus


def _build_dbf(records: list[dict[str, str]], fields: list[tuple[str, str, int]]) -> bytes:
    header_len = 32 + 32 * len(fields) + 1
    rec_len = sum(flen for _, _, flen in fields)
    header = bytearray(32)
    header[0] = 0x03
    struct.pack_into("<I", header, 4, len(records))
    struct.pack_into("<H", header, 8, header_len)
    struct.pack_into("<H", header, 10, rec_len)
    out = bytearray(header)
    for name, ftype, flen in fields:
        fd = bytearray(32)
        fd[: len(name)] = name.encode("ascii")
        fd[11] = ord(ftype)
        fd[16] = flen
        out += fd
    out += b"\x0d"
    for rec in records:
        out += b"\x20"
        for name, _ftype, flen in fields:
            out += rec.get(name, "").ljust(flen).encode("ascii")[:flen]
    return bytes(out)


FIELDS = [("Name", "C", 14), ("Dx", "C", 2), ("Impact", "C", 4)]


def test_read_dbf_parses_records():
    data = _build_dbf(
        [
            {"Name": "Majuro", "Dx": "NO", "Impact": ""},
            {"Name": "Kapingamarangi", "Dx": "D1", "Impact": "(S)"},
        ],
        FIELDS,
    )
    recs = _read_dbf(data)
    assert len(recs) == 2
    assert recs[0]["Name"] == "Majuro"
    assert recs[0]["Dx"] == "NO"
    assert recs[1]["Name"] == "Kapingamarangi"
    assert recs[1]["Dx"] == "D1"
    assert recs[1]["Impact"] == "(S)"


def test_parse_oconus_reads_dbf_from_zip():
    dbf = _build_dbf([{"Name": "Koror", "Dx": "D0", "Impact": "(S)"}], FIELDS)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("20261020_oconus.dbf", dbf)
    recs = parse_oconus(buf.getvalue())
    assert len(recs) == 1
    assert recs[0]["Name"] == "Koror"
    assert recs[0]["Dx"] == "D0"


def test_name_mapping_covers_fas_islands():
    assert USDM_NAME_TO_GEO["Majuro"] == "RMI-MAJ"
    assert USDM_NAME_TO_GEO["Kapingamarangi"] == "FSM-POH-KAP"
    assert USDM_NAME_TO_GEO["Koror"] == "PAL-KOR"
    assert USDM_NAME_TO_GEO["Chuuk Lagoon"] == "FSM-CHUUK"
    # RMI islands the USDM ranks individually are all mapped.
    for name in ("Majuro", "Kwajalein", "Wotje", "Utirik", "Jaluit"):
        assert name in USDM_NAME_TO_GEO
