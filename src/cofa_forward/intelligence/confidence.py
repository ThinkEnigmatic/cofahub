"""Confidence labeling with documented criteria.

Qualitative confidence labels are defined by explicit criteria (see
docs/SCIENTIFIC_METHODS.md). No numerical confidence value is manufactured.
"""

from __future__ import annotations


def qualitative_confidence(
    sample_size: int | None = None,
    data_quality: str | None = None,
    model_agreement: str | None = None,
) -> str:
    """Return a qualitative confidence label from documented criteria.

    * high    — ample sample (>=20), good data quality, and (if applicable) high model agreement.
    * medium  — moderate sample (>=8) and acceptable quality.
    * low     — small sample or limited quality.
    * unknown — cannot assess from available information.
    """
    q = (data_quality or "").lower()
    if sample_size is None and data_quality is None and model_agreement is None:
        return "unknown"
    n = sample_size if sample_size is not None else 0
    if n >= 20 and ("good" in q or "high" in q or q == ""):
        if model_agreement and "high" in model_agreement.lower():
            return "high"
        if model_agreement is None:
            return "high"
    if n >= 8:
        return "medium"
    return "low"


CONFIDENCE_CRITERIA = {
    "high": "ample sample (>=20) and good data quality; high model agreement where applicable",
    "medium": "moderate sample (>=8) and acceptable data quality",
    "low": "small sample or limited data quality",
    "unknown": "insufficient information to assess",
}
