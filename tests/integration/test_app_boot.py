"""Integration tests: app boot with no credentials + end-to-end sample pipeline."""

from __future__ import annotations

import pandas as pd

from cofa_forward.config import get_config
from cofa_forward.geography.registry import GeographyRegistry
from cofa_forward.intelligence.indicators import compute_location_indicators
from cofa_forward.intelligence.report_builder import build_markdown_report
from cofa_forward.intelligence.synthesis import build_statements
from cofa_forward.sample_data import synthetic_daily_rainfall


def test_boots_without_credentials():
    cfg = get_config()
    assert cfg.name == "COFA FORWARD"
    assert cfg.geography_status == "seed"
    # no credentials required
    assert cfg.env("OPEN_METEO_BASE_URL") is None


def test_registry_builds_three_countries():
    cfg = get_config()
    reg = GeographyRegistry(cfg.geography_entities())
    assert len(reg.countries()) == 3
    # four FSM states
    states = reg.of_type("state")
    assert {s.geo_id for s in states} == {"FSM-YAP", "FSM-CHUUK", "FSM-POH", "FSM-KOS"}


def test_sample_rainfall_deterministic_and_shape():
    a = synthetic_daily_rainfall("PAL-KOR", years=30)
    b = synthetic_daily_rainfall("PAL-KOR", years=30)
    pd.testing.assert_series_equal(a, b)
    # 30 years of daily data (~10950+ days)
    assert len(a) > 10000
    assert a.isna().sum() == 0


def test_end_to_end_indicator_pipeline():
    cfg = get_config()
    d = cfg.drought
    daily = synthetic_daily_rainfall("PAL-KOR", years=30)
    ind = compute_location_indicators(
        "PAL-KOR",
        "Koror",
        daily,
        d["baseline_start"],
        d["baseline_end"],
        d["baseline_min_years"],
        d["percentile_categories"],
    )
    assert ind["baseline_valid"] is True
    assert ind["percentile"] is not None
    assert 0.0 <= ind["percentile"] <= 1.0
    assert ind["rolling"]["rain_3m_mm"] is not None


def test_report_pipeline_markdown():
    cfg = get_config()
    d = cfg.drought
    registry = GeographyRegistry(cfg.geography_entities())
    indicators = []
    for e in registry.of_type("country") + registry.of_type("state"):
        daily = synthetic_daily_rainfall(e.geo_id, years=30)
        indicators.append(
            compute_location_indicators(
                e.geo_id,
                e.name,
                daily,
                d["baseline_start"],
                d["baseline_end"],
                d["baseline_min_years"],
                d["percentile_categories"],
            )
        )
    stmts = build_statements(indicators, cfg.enso_current)
    md = build_markdown_report(
        {"report_date": "2026-10-28", "data_cutoff": "2026-10-28T00:00:00Z"},
        [{"title": "Summary", "items": stmts}],
        [
            {"source_id": s.id, "retrieved_at": "—", "status": s.implementation_status}
            for s in cfg.sources()
        ],
        ["gap 1"],
    )
    assert "COFA FORWARD" in md
    assert "Summary" in md
