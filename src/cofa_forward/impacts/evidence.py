"""Evidence and confidence labeling.

Provides a small, documented vocabulary so every substantive conclusion carries
an evidence-quality and confidence label rather than an invented number.
"""

from __future__ import annotations

from dataclasses import dataclass

EVIDENCE_QUALITY = ("documented", "inferred", "modeled", "sample", "none")

# Qualitative confidence labels are defined in docs/SCIENTIFIC_METHODS.md.
CONFIDENCE_LABELS = ("high", "medium", "low", "unknown", "sample")


@dataclass(frozen=True)
class Evidence:
    quality: str
    confidence: str
    source: str | None = None

    def __post_init__(self) -> None:
        if self.quality not in EVIDENCE_QUALITY:
            raise ValueError(f"invalid evidence_quality: {self.quality}")
        if self.confidence not in CONFIDENCE_LABELS:
            raise ValueError(f"invalid confidence: {self.confidence}")


def evidence_label(quality: str, confidence: str, source: str | None = None) -> dict:
    """Return a structured evidence/confidence label dict."""
    e = Evidence(quality=quality, confidence=confidence, source=source)
    return {
        "evidence_quality": e.quality,
        "confidence": e.confidence,
        "source": e.source,
    }
