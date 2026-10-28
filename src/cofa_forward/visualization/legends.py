"""Legend and unit-label helpers."""

from __future__ import annotations


def unit_label(metric_unit: str, imperial: bool) -> str:
    """Return a presentation unit label for a metric unit."""
    from ..units import display_unit

    return display_unit(metric_unit, imperial)


def legend_text(units: str, valid_time: str, init_time: str, source: str, resolution: str) -> str:
    """One-line source/metadata caption for any layer."""
    parts = [f"Units: {units}"]
    if valid_time:
        parts.append(f"Valid: {valid_time}")
    if init_time:
        parts.append(f"Init: {init_time}")
    if source:
        parts.append(f"Source: {source}")
    if resolution:
        parts.append(f"Resolution: {resolution}")
    return " · ".join(parts)
