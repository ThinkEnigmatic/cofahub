"""Shared regional map (Plotly, no external tile/API key required)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..geography.registry import GeographyRegistry

# Consistent entity styling (one art direction across the app).
ENTITY_STYLE = {
    "country": {"color": "#1f2937", "symbol": "square", "size": 14, "label": "Country"},
    "state": {"color": "#2563eb", "symbol": "diamond", "size": 11, "label": "State"},
    "island": {"color": "#0891b2", "symbol": "circle", "size": 9, "label": "Island"},
    "atoll": {"color": "#059669", "symbol": "circle", "size": 9, "label": "Atoll"},
    "monitoring_location": {
        "color": "#d97706",
        "symbol": "cross",
        "size": 8,
        "label": "Monitoring location",
    },
}

_THEME = {
    "bg": "#ffffff",
    "land": "#e8e4dc",
    "coast": "#94a3b8",
    "font": "#0f172a",
    "grid": "#e2e8f0",
}


def region_map(
    registry: GeographyRegistry,
    center: tuple[float, float] = (6.5, 152.0),
    zoom: float = 4.0,
    title: str | None = None,
) -> go.Figure:
    """Base regional map with all registry entities layered by type."""
    fig = go.Figure()

    for etype, style in ENTITY_STYLE.items():
        ents = registry.of_type(etype)
        if not ents:
            continue
        fig.add_trace(
            go.Scattergeo(
                lat=[e.latitude for e in ents],
                lon=[e.longitude for e in ents],
                mode="markers",
                name=style["label"],
                marker=dict(
                    size=style["size"],
                    color=style["color"],
                    symbol=style["symbol"],
                    line=dict(width=0.5, color="#ffffff"),
                ),
                text=[f"<b>{e.name}</b><br>{e.geo_id}<br>{e.entity_type}" for e in ents],
                hoverinfo="text",
            )
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=16)) if title else None,
        geo=dict(
            projection_type="natural earth",
            center=dict(lat=center[0], lon=center[1]),
            projection_scale=zoom,
            showland=True,
            landcolor=_THEME["land"],
            coastlinecolor=_THEME["coast"],
            showocean=True,
            oceancolor="#f4f7fb",
            showcountries=False,
            showframe=False,
            bgcolor=_THEME["bg"],
        ),
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        height=520,
        paper_bgcolor=_THEME["bg"],
        font=dict(color=_THEME["font"], family="Inter, -apple-system, sans-serif"),
    )
    return fig


def metric_map(
    registry: GeographyRegistry,
    values: dict[str, float],
    center: tuple[float, float] = (6.5, 152.0),
    zoom: float = 4.0,
    title: str = "",
    colorbar_title: str = "",
    colorscale: str = "YlOrRd",
) -> go.Figure:
    """Regional map with entities colored by a scalar metric.

    ``values`` maps geo_id -> scalar. Missing values are shown grey.
    """
    df = registry.to_dataframe()
    df["value"] = df["geo_id"].map(values)

    fig = go.Figure(
        go.Scattergeo(
            lat=df["latitude"],
            lon=df["longitude"],
            mode="markers",
            marker=dict(
                size=11,
                color=df["value"],
                colorscale=colorscale,
                cmin=0,
                cmax=max(df["value"].max(), 1.0) if df["value"].notna().any() else 1.0,
                showscale=True,
                colorbar=dict(title=colorbar_title, thickness=12),
                line=dict(width=0.5, color="#ffffff"),
            ),
            text=[
                f"<b>{r['name']}</b><br>{r['geo_id']}"
                + (
                    f"<br>{colorbar_title}: {r['value']:.1f}"
                    if pd.notna(r["value"])
                    else "<br>no data"
                )
                for _, r in df.iterrows()
            ],
            hoverinfo="text",
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        geo=dict(
            projection_type="natural earth",
            center=dict(lat=center[0], lon=center[1]),
            projection_scale=zoom,
            showland=True,
            landcolor=_THEME["land"],
            coastlinecolor=_THEME["coast"],
            showocean=True,
            oceancolor="#f4f7fb",
            showcountries=False,
            showframe=False,
            bgcolor=_THEME["bg"],
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        height=520,
        paper_bgcolor=_THEME["bg"],
        font=dict(color=_THEME["font"]),
    )
    return fig
