"""Configuration validation tests."""

from __future__ import annotations

import pytest

from cofa_forward.config import Config, ConfigError, get_config


def test_config_loads(config):
    assert config.name == "COFA FORWARD"
    assert config.default_units == "metric"


def test_geography_entities_nonempty(config):
    ents = config.geography_entities()
    assert len(ents) >= 3
    ids = {e.geo_id for e in ents}
    assert {"PAL", "FSM", "RMI"} <= ids


def test_sources_parsed(config):
    sources = config.sources()
    assert any(s.id == "open-meteo-forecast" for s in sources)
    om = next(s for s in sources if s.id == "open-meteo-forecast")
    assert om.implementation_status == "implemented_and_tested"


def test_enso_episodes(config):
    eps = config.enso_episodes()
    assert any(e.id == "2015-16" for e in eps)
    assert config.enso_current["status"] == "unavailable"


def test_alert_thresholds(config):
    alerts = config.alert_thresholds()
    assert len(alerts) >= 1
    assert all(a.threshold.get("operator") in ("gt", "lt", "gte", "lte", "eq") for a in alerts)


def test_missing_config_raises(tmp_path):
    with pytest.raises(ConfigError):
        Config(root=tmp_path)  # no config dir


def test_get_config_cached():
    a = get_config()
    b = get_config()
    assert a is b
