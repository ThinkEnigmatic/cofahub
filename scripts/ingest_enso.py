"""ENSO ingestion — PLANNED (Phase 3).

Authoritative ENSO classification must come from NOAA CPC. This placeholder
documents the intent and exits without importing anything.
"""

from __future__ import annotations


def main() -> int:
    print("ENSO ingestion is PLANNED (Phase 3).")
    print("Target: NOAA CPC Oceanic Nino Index (oni.ascii.txt).")
    print("Until then, current ENSO status is reported as 'unavailable' (no phase assumed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
