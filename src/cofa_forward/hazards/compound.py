"""Compound (co-occurring) hazard flags.

Single indicators understate atoll risk: the 2024 RMI emergency was a *drought
and inundation* event at once. This module flags co-occurrence across the
independent indicators the app already computes — meteorological drought
(quintile / PEAC), significant wave height, and tropical-cyclone proximity.

Thresholds are documented planning defaults (not official trigger values). A flag
is a *co-occurrence warning*, never a government alert.
"""

from __future__ import annotations

# Significant wave height above which outer-island transport/fishing is impaired.
_WAVE_HIGH_M = 2.5
# Distance within which a tropical system compounds a drought-stressed atoll.
_CYCLONE_PROXIMITY_KM = 300.0


def compound_flags(
    *,
    drought_quintile: str | None,
    peac_index: str | None,
    wave_height_m: float | None,
    cyclone_km: float | None = None,
    cyclone_name: str | None = None,
) -> list[str]:
    """Return active compound-hazard flags (documented thresholds, advisory only)."""
    dry = drought_quintile in ("Drier", "Dry") or peac_index == "Red"
    high_waves = wave_height_m is not None and wave_height_m >= _WAVE_HIGH_M
    flags: list[str] = []

    if dry and high_waves:
        flags.append(
            "Drought + large seas (≥2.5 m): reduced rainfall and rough seas together "
            "stress outer-island water, fishing and transport."
        )
    if dry and cyclone_km is not None and cyclone_km <= _CYCLONE_PROXIMITY_KM:
        name = f" ({cyclone_name})" if cyclone_name else ""
        flags.append(
            f"Drought + tropical cyclone within {_CYCLONE_PROXIMITY_KM:.0f} km{name}: "
            "a drought-stressed atoll facing a storm is a compound shock."
        )
    if peac_index == "Red" and high_waves:
        flags.append(
            "PEAC Red (<101.6 mm) + large seas: water shortage coincident with rough seas."
        )
    return flags
