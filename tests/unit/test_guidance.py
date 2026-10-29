"""National drought plans / guidance catalog tests."""

from __future__ import annotations

from cofa_forward.guidance.national_plans import NATIONAL_PLANS, fas_plans


def test_catalog_is_populated_and_provenanced():
    assert len(NATIONAL_PLANS) >= 4
    for p in NATIONAL_PLANS:
        assert p["title"]
        assert p["url"].startswith("http")
        assert p["verification_status"] == "verified"
        assert p["extraction_method"]
        assert p["key_facts"]


def test_fas_plans_filter_by_country():
    rmi = fas_plans("MH")
    assert rmi, "expected RMI plans"
    assert all(p["country_code"] == "MH" for p in rmi)


def test_rmi_zone_fact_present():
    rmi = fas_plans("MH")
    zone_fact = next(f for p in rmi for f in p["key_facts"] if "Zone 1" in f or "Zone 2" in f)
    assert "8" in zone_fact  # >8°N / 6-8°N


def test_fsm_ndprp_endorsed_2026():
    fsm = fas_plans("FM")
    assert any(p["doc_id"] == "fsm-ndprp-2026" for p in fsm)
    ndprp = next(p for p in fsm if p["doc_id"] == "fsm-ndprp-2026")
    assert ndprp["date"] == "2026-08-22"
    assert any("pillar" in f.lower() for f in ndprp["key_facts"])


def test_palau_stage_plan():
    palau = fas_plans("PW")
    assert any("Stage 1" in f for p in palau for f in p["key_facts"])
