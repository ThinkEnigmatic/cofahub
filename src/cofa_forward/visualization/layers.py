"""Map layer definitions.

Each layer carries its own metadata so the UI can show a legend, units, valid
time, source, and spatial resolution independently. Overlays that combine layers
with incompatible time periods or resolutions must explain the difference.
"""

from __future__ import annotations

LAYERS = [
    {
        "id": "geography",
        "name": "FAS geography (seed)",
        "kind": "vector",
        "units": None,
        "source": "config/geography.yaml (seed)",
        "resolution": "approximate point locations",
        "note": "Seed registry; not a validated boundary inventory.",
    },
    {
        "id": "forecast_precipitation",
        "name": "Forecast precipitation",
        "kind": "raster",
        "units": "mm",
        "source": "Open-Meteo forecast",
        "resolution": "~11 km model grid",
        "note": "Model output; individual-atoll conditions may differ.",
    },
    {
        "id": "rainfall_anomaly",
        "name": "Rainfall anomaly",
        "kind": "raster",
        "units": "% of normal",
        "source": "ERA5 archive (computed)",
        "resolution": "~25 km reanalysis",
        "note": "Requires valid baseline.",
    },
    {
        "id": "cyclone_tracks",
        "name": "Tropical cyclone tracks",
        "kind": "vector",
        "units": "kt",
        "source": "sample / IBTrACS (planned)",
        "resolution": "point track",
        "note": "Sample data until IBTrACS is wired in.",
    },
]


def available_layers() -> list[dict]:
    return LAYERS


def get_layer(layer_id: str) -> dict | None:
    for lyr in LAYERS:
        if lyr["id"] == layer_id:
            return lyr
    return None
