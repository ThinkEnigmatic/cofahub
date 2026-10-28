"""Chart builders (Plotly)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_PALETTE = ["#2563eb", "#0891b2", "#059669", "#d97706", "#dc2626", "#7c3aed"]

_LINE = dict(width=2)


def rainfall_timeseries(
    monthly: pd.Series,
    climatology: pd.Series | None = None,
    title: str = "Monthly rainfall",
) -> go.Figure:
    """Monthly rainfall bars with an optional climatology overlay line."""
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    fig.add_trace(
        go.Bar(x=monthly.index, y=monthly.values, name="Monthly total (mm)", marker_color="#2563eb")
    )
    if climatology is not None and len(climatology):
        # climatology is per calendar month; expand to the monthly index
        clim = pd.Series(monthly.index.map(lambda t: climatology.get(t.month)), index=monthly.index)
        fig.add_trace(
            go.Scatter(
                x=monthly.index,
                y=clim.values,
                name="Climatology (mm)",
                mode="lines",
                line=dict(color="#dc2626", width=2, dash="dash"),
            )
        )
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=360,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        yaxis_title="mm",
    )
    return fig


def forecast_chart(hourly: pd.DataFrame, title: str = "Hourly forecast") -> go.Figure:
    """Temperature (line) + precipitation (bars) for an hourly forecast frame."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if "temperature_2m" in hourly:
        fig.add_trace(
            go.Scatter(
                x=hourly.index,
                y=hourly["temperature_2m"],
                name="Temperature (°C)",
                line=dict(color="#dc2626", **_LINE),
            ),
            secondary_y=False,
        )
    if "precipitation" in hourly:
        fig.add_trace(
            go.Bar(
                x=hourly.index,
                y=hourly["precipitation"],
                name="Precipitation (mm)",
                marker_color="#2563eb",
                opacity=0.6,
            ),
            secondary_y=True,
        )
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=340,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_yaxes(title_text="°C", secondary_y=False)
    fig.update_yaxes(title_text="mm", secondary_y=True)
    return fig


def rolling_totals_chart(
    rolling: pd.DataFrame, title: str = "Rolling rainfall totals"
) -> go.Figure:
    """Line chart of rolling N-month rainfall totals."""
    fig = go.Figure()
    for i, col in enumerate(rolling.columns):
        fig.add_trace(
            go.Scatter(
                x=rolling.index,
                y=rolling[col],
                name=col,
                mode="lines",
                line=dict(color=_PALETTE[i % len(_PALETTE)], width=2),
            )
        )
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=340,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        yaxis_title="mm",
    )
    return fig


def track_map(
    tracks: pd.DataFrame,
    center: tuple[float, float] = (6.5, 152.0),
    zoom: float = 4.0,
    title: str = "Tropical cyclone tracks",
) -> go.Figure:
    """Plot storm tracks as lines (with markers), one trace per storm."""
    fig = go.Figure()
    for sid, grp in tracks.groupby("storm_id"):
        grp = grp.sort_values("time")
        hover = [
            f"{sid}<br>{t}<br>{w} kt" for t, w in zip(grp["time"], grp["wind_kt"], strict=True)
        ]
        fig.add_trace(
            go.Scattergeo(
                lat=grp["lat"],
                lon=grp["lon"],
                mode="lines+markers",
                name=str(sid),
                line=dict(width=2),
                marker=dict(size=4),
                text=hover,
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
            landcolor="#e8e4dc",
            coastlinecolor="#94a3b8",
            showocean=True,
            oceancolor="#f4f7fb",
            showcountries=False,
            showframe=False,
            bgcolor="#ffffff",
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        height=460,
        paper_bgcolor="#ffffff",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
    )
    return fig
