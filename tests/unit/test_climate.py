"""ENSO state, episodes, and analog-engine tests."""

from __future__ import annotations

import math

from cofa_forward.climate.analogs import rank_analogs, similarity
from cofa_forward.climate.enso_state import enso_state_from_config
from cofa_forward.climate.episodes import match_episodes
from cofa_forward.schemas import EnsoEpisode


def _episodes():
    return [
        EnsoEpisode(
            id="1997-98",
            phase="el_nino",
            start="1997-05-01",
            peak="1997-11-15",
            end="1998-05-31",
            intensity="very_strong",
        ),
        EnsoEpisode(
            id="2023-24",
            phase="el_nino",
            start="2023-06-01",
            peak="2023-12-15",
            end="2024-05-31",
            intensity="strong",
        ),
        EnsoEpisode(id="2026-27", phase=None, start=None, end=None),
    ]


def test_match_episodes():
    eps = _episodes()
    hit = match_episodes(eps, "1997-12-01")
    assert [e.id for e in hit] == ["1997-98"]
    # unconfirmed evolving episode (no dates) is never matched
    assert match_episodes(eps, "2026-12-01") == []


def test_enso_state_unavailable():
    st = enso_state_from_config({"status": "unavailable", "phase": None})
    assert not st.is_available
    assert "unavailable" in st.display()


def test_enso_state_official():
    st = enso_state_from_config(
        {"status": "official", "phase": "el_nino", "as_of": "2026-10-01", "source": "CPC"}
    )
    assert st.is_available
    assert "el_nino" in st.display()


def test_similarity_identical_is_one():
    current = {"enso": 1.0, "anomaly": 0.5}
    sim, detail = similarity(
        current, current, {"enso": 1.0, "anomaly": 1.0}, {"enso": 2.0, "anomaly": 2.0}
    )
    assert math.isclose(sim, 1.0)


def test_similarity_missing_feature_skipped():
    current = {"enso": 1.0}
    cand = {"anomaly": 0.5}
    sim, detail = similarity(
        current, cand, {"enso": 1.0, "anomaly": 1.0}, {"enso": 2.0, "anomaly": 2.0}
    )
    assert detail["missing"] == ["enso", "anomaly"]
    assert sim == 0.0  # no comparable features


def test_rank_analogs_orders():
    current = {"enso": 1.0, "anomaly": 0.0}
    candidates = [
        {"id": "A", "enso": 1.0, "anomaly": 0.0},
        {"id": "B", "enso": -1.0, "anomaly": 5.0},
    ]
    ranked = rank_analogs(
        current, candidates, {"enso": 1.0, "anomaly": 1.0}, {"enso": 2.0, "anomaly": 10.0}
    )
    assert ranked[0]["id"] == "A"
    assert ranked[0]["similarity"] > ranked[1]["similarity"]
