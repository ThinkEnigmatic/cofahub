"""Interactive Leaflet maps (folium) with real satellite basemaps.

The FAS atolls are a few kilometres across; the original Plotly ``scattergeo``
map rendered them as invisible dots on a featureless ocean. These folium maps
use free, keyless satellite basemaps so the islands are actually visible:

* **Esri World Imagery** — high-resolution commercial-satellite mosaic (zoom 19),
  the best free choice for seeing individual atolls.
* **NASA GIBS** BlueMarble / MODIS Terra / MODIS Aqua / VIIRS — the official
  NASA EOSDIS Global Imagery Browse Services, keyless, ~250 m daily true-colour.

Basemaps are chosen client-side via a Leaflet layer control (no API key, no
backend tile proxy). Tiles load from the user's browser directly against the
public GIBS/Esri endpoints, so nothing here adds server load or credentials.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import folium
import pandas as pd

from ..geography.registry import GeographyRegistry

# Consistent entity styling (shared art direction with the Plotly map).
ENTITY_STYLE = {
    "country": {"color": "#1f2937", "fill": True, "radius": 8, "label": "Country"},
    "state": {"color": "#2563eb", "fill": True, "radius": 6, "label": "State"},
    "island": {"color": "#0891b2", "fill": True, "radius": 5, "label": "Island"},
    "atoll": {"color": "#059669", "fill": True, "radius": 5, "label": "Atoll"},
    "monitoring_location": {
        "color": "#d97706",
        "fill": True,
        "radius": 4,
        "label": "Monitoring location",
    },
}

_GIBS_BASE = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best"

# Keyless satellite basemaps. Each maps a friendly name -> dict with a tile URL
# template (folium `{z}/{x}/{y}`) and metadata. GIBS URLs use its REST WMTS path
# `{layer}/default/{date}/{TileMatrixSet}/{z}/{y}/{x}.jpg`.
#
# NOTE on GIBS tile-matrix-set names: each layer serves a *specific* TMS
# (Level8/Level9), and the zoom is capped accordingly. Esri World Imagery is the
# only full-zoom option (to ~19) — the rest are ~250 m daily true-colour.
BASEMAPS: dict[str, dict] = {
    "Esri satellite (hi-res)": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Esri, Maxar, Earthstar Geographics",
        "max_native_zoom": 19,
        "max_zoom": 19,
    },
    "NASA BlueMarble": {
        "url": (
            _GIBS_BASE
            + "/BlueMarble_ShadedRelief_Bathymetry/default/2013-01-01/"
            + "GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg"
        ),
        "attr": "NASA GIBS / Blue Marble",
        "max_native_zoom": 8,
        "max_zoom": 8,
    },
    "NASA MODIS Terra (daily)": {
        "url": None,  # filled at call time with the latest available date
        "layer": "MODIS_Terra_CorrectedReflectance_TrueColor",
        "tms": "GoogleMapsCompatible_Level9",
        "attr": "NASA GIBS / MODIS Terra",
        "max_native_zoom": 9,
        "max_zoom": 9,
        "dated": True,
    },
    "NASA MODIS Aqua (daily)": {
        "url": None,
        "layer": "MODIS_Aqua_CorrectedReflectance_TrueColor",
        "tms": "GoogleMapsCompatible_Level9",
        "attr": "NASA GIBS / MODIS Aqua",
        "max_native_zoom": 9,
        "max_zoom": 9,
        "dated": True,
    },
    "NASA VIIRS (daily)": {
        "url": None,
        "layer": "VIIRS_SNPP_CorrectedReflectance_TrueColor",
        "tms": "GoogleMapsCompatible_Level9",
        "attr": "NASA GIBS / VIIRS Suomi-NPP",
        "max_native_zoom": 9,
        "max_zoom": 9,
        "dated": True,
    },
    "OpenStreetMap (streets)": {
        "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": "© OpenStreetMap contributors",
        "max_native_zoom": 19,
        "max_zoom": 19,
    },
}

_DEFAULT_BASEMAP = "Esri satellite (hi-res)"


def _gibs_date(offset_days: int = 2) -> str:
    """Latest plausible GIBS true-colour date.

    Daily true-colour composites are published with a ~1-2 day latency; using a
    recent date keeps tiles valid without a server-side availability probe.
    """
    d = datetime.now(UTC) - timedelta(days=offset_days)
    return d.strftime("%Y-%m-%d")


def _resolved_basemap(name: str) -> dict:
    """Return a basemap spec with any ``dated`` GIBS layer resolved to a URL."""
    spec = dict(BASEMAPS[name])
    if spec.get("dated") or spec.get("url") is None:
        date = _gibs_date()
        spec["url"] = (
            f"{_GIBS_BASE}/{spec['layer']}/default/{date}/{spec['tms']}/{{z}}/{{y}}/{{x}}.jpg"
        )
    return spec


def _add_basemaps(m: folium.Map) -> None:
    """Attach all basemaps and a layer control (basemaps are mutually exclusive)."""
    for name in BASEMAPS:
        resolved = _resolved_basemap(name)
        folium.TileLayer(
            tiles=resolved["url"],
            name=name,
            attr=resolved["attr"],
            max_native_zoom=resolved.get("max_native_zoom", 19),
            max_zoom=resolved.get("max_zoom", 19),
            overlay=False,
            control=True,
            show=(name == _DEFAULT_BASEMAP),
        ).add_to(m)
    folium.LayerControl(collapsed=False, position="topright").add_to(m)


_BOUNDARY_STYLE = {
    "color": "#0ea5e9",
    "weight": 1.4,
    "fillColor": "#0ea5e9",
    "fillOpacity": 0.06,
}


def _add_boundaries(m: folium.Map, boundaries: list[dict] | None) -> None:
    """Render administrative boundary polygons as a single GeoJSON overlay.

    ``boundaries`` is a list of ``{geo_id, name, country_code, geometry}`` records
    (see ``ui.state.get_boundaries``). Point markers for the same entities remain
    the primary interactive layer; polygons are the spatial context.
    """
    if not boundaries:
        return
    features = []
    for b in boundaries:
        if not b.get("geometry"):
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "name": b.get("name", ""),
                    "country": b.get("country_code", ""),
                },
                "geometry": b["geometry"],
            }
        )
    if not features:
        return
    folium.GeoJson(
        {"type": "FeatureCollection", "features": features},
        name="Administrative boundaries",
        style_function=lambda _f: _BOUNDARY_STYLE,
        popup=folium.GeoJsonPopup(fields=["name", "country"], labels=True, aliases=["", "Country"]),
        tooltip=folium.GeoJsonTooltip(fields=["name"], labels=False),
        show=True,
    ).add_to(m)


def _add_entities(m: folium.Map, registry: GeographyRegistry) -> None:
    """Layer registry entities onto the map, styled by type, with popups."""
    for etype, style in ENTITY_STYLE.items():
        for e in registry.of_type(etype):
            popup = (
                f"<b>{e.name}</b><br>"
                f"{e.geo_id} · {etype.replace('_', ' ')}<br>"
                f"{e.latitude:.3f}°N, {e.longitude:.3f}°E"
            )
            folium.CircleMarker(
                location=(e.latitude, e.longitude),
                radius=style["radius"],
                color=style["color"],
                fill=style["fill"],
                fill_opacity=0.85,
                weight=1.5,
                popup=folium.Popup(popup, max_width=240),
                tooltip=e.name,
            ).add_to(m)


def _add_tracks(m: folium.Map, tracks: pd.DataFrame) -> None:
    """Plot storm tracks as polylines (one per storm) with start markers."""
    if tracks is None or tracks.empty:
        return
    for sid, grp in tracks.groupby("storm_id"):
        grp = grp.sort_values("time")
        points = list(zip(grp["lat"], grp["lon"], strict=True))
        if not points:
            continue
        folium.PolyLine(
            points,
            color="#dc2626",
            weight=2.5,
            opacity=0.9,
            tooltip=f"{sid} — {len(points)} points",
        ).add_to(m)
        folium.CircleMarker(
            points[0],
            radius=3,
            color="#dc2626",
            fill=True,
            fill_opacity=1.0,
            tooltip=f"{sid} start",
        ).add_to(m)


def region_map(
    registry: GeographyRegistry,
    center: tuple[float, float] = (6.5, 152.0),
    zoom: float = 5.0,
    title: str | None = None,
    boundaries: list[dict] | None = None,
) -> folium.Map:
    """Regional map of FAS entities over a satellite basemap (layer-switchable).

    ``boundaries``, when provided, adds an administrative-boundary polygon overlay
    beneath the point markers.
    """
    m = folium.Map(
        location=list(center),
        zoom_start=int(zoom),
        control_scale=True,
        tiles=None,
    )
    _add_basemaps(m)
    _add_boundaries(m, boundaries)
    _add_entities(m, registry)
    return m


def track_map(
    tracks: pd.DataFrame,
    center: tuple[float, float] = (6.5, 152.0),
    zoom: float = 5.0,
    title: str | None = None,
) -> folium.Map:
    """Storm tracks + FAS entities over a satellite basemap."""
    m = folium.Map(
        location=list(center),
        zoom_start=int(zoom),
        control_scale=True,
        tiles=None,
    )
    _add_basemaps(m)
    _add_tracks(m, tracks)
    return m


_COLORSCALES = {
    "YlOrRd": "YlOrRd_09",
    "RdYlBu": "RdYlBu_11",
    "RdYlGn": "RdYlGn_11",
    "YlGnBu": "YlGnBu_09",
    "RdBu": "RdBu_11",
}


def metric_map(
    registry: GeographyRegistry,
    values: dict[str, float],
    center: tuple[float, float] = (6.5, 152.0),
    zoom: float = 5.0,
    title: str = "",
    colorbar_title: str = "",
    colorscale: str = "YlOrRd",
) -> folium.Map:
    """Regional map with entities coloured by a scalar metric.

    ``values`` maps geo_id -> scalar. Missing values are shown grey. Plotly-style
    ``colorscale`` names are mapped onto a matching branca colour ramp; a
    diverging ramp (RdYlBu/RdBu/RdYlGn) is used for signed metrics such as
    rainfall anomaly.
    """
    import branca.colormap as cm

    m = folium.Map(
        location=list(center),
        zoom_start=int(zoom),
        control_scale=True,
        tiles=None,
    )
    _add_basemaps(m)

    present = {k: v for k, v in values.items() if pd.notna(v)}
    if present:
        vmin, vmax = min(present.values()), max(present.values())
        if vmin == vmax:
            vmax = vmin + 1.0
        ramp = getattr(cm.linear, _COLORSCALES.get(colorscale, "YlOrRd_09"))
        colormap = ramp.scale(vmin, vmax)
        colormap.caption = colorbar_title or "value"
        colormap.add_to(m)
    else:
        colormap = None

    for e in registry.all():
        v = values.get(e.geo_id)
        if v is None or pd.isna(v):
            color, label = "#9ca3af", f"{e.name}: no data"
        else:
            color = colormap(v) if colormap else "#b91c1c"
            label = f"{e.name}: {v:.1f}"
        folium.CircleMarker(
            location=(e.latitude, e.longitude),
            radius=6,
            color=color,
            fill=True,
            fill_opacity=0.9,
            weight=1.5,
            popup=folium.Popup(f"<b>{e.name}</b><br>{label}", max_width=240),
            tooltip=e.name,
        ).add_to(m)
    return m
