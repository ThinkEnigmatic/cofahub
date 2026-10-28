"""Current ENSO state.

The authoritative current-state classification comes from a configured source
(NOAA CPC ONI, planned). Until then we expose an explicit "unavailable" state —
we never infer a phase from an old report or a model guess.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EnsoState:
    status: str  # "official" | "unavailable" | "stale"
    phase: str | None
    as_of: str | None
    source: str | None
    note: str = ""

    @property
    def is_available(self) -> bool:
        return self.status == "official" and self.phase is not None

    def display(self) -> str:
        if self.is_available:
            return f"{self.phase} (as of {self.as_of}, source: {self.source})"
        if self.status == "stale" and self.phase is not None:
            return f"{self.phase} (stale, as of {self.as_of})"
        return "unavailable — no authoritative ENSO source configured"


def enso_state_from_config(current: dict[str, Any]) -> EnsoState:
    """Build an ``EnsoState`` from the ``current_state`` block of enso.yaml."""
    return EnsoState(
        status=current.get("status", "unavailable"),
        phase=current.get("phase"),
        as_of=current.get("as_of"),
        source=current.get("source"),
        note=current.get("note", ""),
    )
