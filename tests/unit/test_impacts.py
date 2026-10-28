"""Impact catalog and evidence tests."""

from __future__ import annotations

import pandas as pd
import pytest

from cofa_forward.impacts.event_catalog import load_catalog
from cofa_forward.impacts.evidence import Evidence, evidence_label
from cofa_forward.impacts.impact_analysis import summarize_by_country


def _df():
    return pd.DataFrame(
        [
            {
                "event_id": "E1",
                "hazard_type": "drought",
                "country": "Palau",
                "geo_id": "PAL",
                "enso_episode_id": "2015-16",
            },
            {
                "event_id": "E2",
                "hazard_type": "tropical_cyclone",
                "country": "FSM",
                "geo_id": "FSM-CHUUK",
                "enso_episode_id": "1997-98",
            },
        ]
    )


def test_load_catalog_and_filter():
    cat = load_catalog(_df())
    assert len(cat.by_country("Palau")) == 1
    assert len(cat.by_hazard("tropical_cyclone")) == 1
    assert len(cat.by_enso_episode("1997-98")) == 1


def test_load_catalog_requires_columns():
    with pytest.raises(ValueError):
        load_catalog(pd.DataFrame({"foo": [1]}))


def test_summarize_by_country():
    cat = load_catalog(_df())
    summ = summarize_by_country(cat)
    assert len(summ) == 2


def test_evidence_validation():
    e = Evidence("documented", "high")
    assert e.quality == "documented"
    with pytest.raises(ValueError):
        Evidence("bogus", "high")


def test_evidence_label():
    lab = evidence_label("inferred", "medium", "src")
    assert lab["evidence_quality"] == "inferred"
    assert lab["source"] == "src"
