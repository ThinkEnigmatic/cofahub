"""Deterministic synthesis of evidence-linked statements.

Every generated statement carries an ``evidence_type`` so the UI and reports can
distinguish observed, forecast, official, historical, modeled, and analyst
statements. No probabilities are invented.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVIDENCE_TYPES = ("observed", "forecast", "official", "historical", "modeled", "analyst")


@dataclass(frozen=True)
class Statement:
    text: str
    evidence_type: str
    source: str | None = None
    provenance: dict[str, Any] | None = None


def build_statements(indicators: list[dict], enso_state: dict[str, Any]) -> list[dict]:
    """Produce evidence-linked summary statements from location indicators.

    ``enso_state`` is a dict with ``status``, ``phase``, ``as_of``, ``source``.
    """
    out: list[dict] = []

    # ENSO status
    if enso_state.get("status") == "official" and enso_state.get("phase"):
        out.append(
            {
                "text": f"Official ENSO status is {enso_state['phase']} "
                f"(as of {enso_state.get('as_of')}).",
                "evidence_type": "official",
                "source": enso_state.get("source"),
            }
        )
    else:
        out.append(
            {
                "text": "No authoritative ENSO classification is currently available; "
                "ENSO status is not assumed.",
                "evidence_type": "analyst",
                "source": None,
            }
        )

    # Rainfall / drought flags from computed indicators
    valid = [i for i in indicators if i.get("baseline_valid")]
    flagged = [i for i in valid if i.get("percentile") is not None and i["percentile"] < 0.2]
    if flagged:
        names = ", ".join(i["name"] for i in flagged[:5])
        out.append(
            {
                "text": f"Rainfall in the lowest 20th percentile at: {names}.",
                "evidence_type": "observed",
                "source": "computed percentile indicator",
            }
        )
    if valid:
        driest = min(valid, key=lambda i: i.get("percentile", 1.0))
        out.append(
            {
                "text": f"Lowest relative rainfall among baseline-valid locations is "
                f"{driest['name']} ({driest['percentile']:.0%} percentile).",
                "evidence_type": "observed",
                "source": "computed percentile indicator",
            }
        )

    n_invalid = len(indicators) - len(valid)
    if n_invalid:
        out.append(
            {
                "text": f"{n_invalid} location(s) lack a sufficient climatological baseline "
                "for anomaly/percentile analysis.",
                "evidence_type": "analyst",
                "source": "baseline validity check",
            }
        )

    return out


def statement_list(stmts: list[dict]) -> list[Statement]:
    return [
        Statement(**{k: s[k] for k in ("text", "evidence_type", "source", "provenance") if k in s})
        for s in stmts
    ]
