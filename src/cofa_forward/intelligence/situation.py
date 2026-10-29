"""Deterministic live situation brief + alert summary.

Pulls the already-computed live indicators into a single readable summary and a
set of threshold-alert lines — no language model, no fabrication. Each line is
tagged with its evidence type and source, and a missing indicator is stated as
missing rather than guessed.
"""

from __future__ import annotations

from typing import Any


def drought_alert_summary(status: dict[str, Any]) -> list[str]:
    """Alert lines from a drought-monitor status (quintile / PEAC / D0-D4)."""
    alerts: list[str] = []
    if not status:
        return alerts
    if status.get("peac_index") == "Red":
        alerts.append("PEAC 4/8-inch Index is RED (<101.6 mm) — drought concern.")
    elif status.get("peac_index") == "Yellow":
        alerts.append("PEAC 4/8-inch Index is YELLOW (101.6–203.2 mm) — adequate.")
    d0 = status.get("d0_d4")
    if d0 in ("D1", "D2", "D3", "D4"):
        alerts.append(f"Drought level {d0} (precipitation percentile below the {d0[1:]}0th).")
    q = status.get("quintile")
    if q in ("Drier", "Dry"):
        alerts.append(f"Rainfall Index '{q}' (latest month below the 40th percentile).")
    return alerts


def build_live_sections(
    *,
    enso: dict[str, Any] | None,
    active_storms: dict[str, Any] | None,
    drought: dict[str, Any] | None,
    sea_level: dict[str, Any] | None,
    marine: dict[str, Any] | None,
    compound: list[str],
) -> list[dict[str, Any]]:
    """Assemble report sections from live indicators (each item evidence-tagged)."""
    sections: list[dict[str, Any]] = []

    enso_items = []
    if enso and enso.get("ok"):
        latest = enso["latest"]
        enso_items.append(
            {
                "text": (
                    f"ONI {latest['season']} {latest['year']} = {latest['anom']:+.2f} °C "
                    f"(derived phase {enso['phase']})."
                ),
                "evidence_type": "observed",
                "source": "NOAA CPC ONI",
            }
        )
    sections.append({"title": "ENSO", "items": enso_items or _missing("ENSO (ONI)")})

    storm_items = []
    if active_storms and active_storms.get("ok"):
        n = active_storms.get("n_active", 0)
        storm_items.append(
            {
                "text": f"{n} active western-North-Pacific tropical cyclone(s).",
                "evidence_type": "observed",
                "source": "JMA RSMC Tokyo",
            }
        )
    sections.append(
        {"title": "Tropical cyclones", "items": storm_items or _missing("active storms")}
    )

    drought_items = []
    if drought and drought.get("ok") and drought.get("status"):
        s = drought["status"]
        drought_items.append(
            {
                "text": (
                    f"{s.get('latest_month')}: {s.get('monthly_mm', 'n/a'):.0f} mm vs "
                    f"{s.get('clim_median_mm', 'n/a'):.0f} mm median — Rainfall Index "
                    f"'{s.get('quintile', 'n/a')}', PEAC '{s.get('peac_index', 'n/a')}'."
                ),
                "evidence_type": "observed",
                "source": drought.get("source", "ERA5"),
            }
        )
        drought_items += [
            {"text": a, "evidence_type": "analyst", "source": "drought monitor"}
            for a in drought_alert_summary(s)
        ]
    sections.append({"title": "Drought", "items": drought_items or _missing("drought monitor")})

    sea_items = []
    if sea_level and sea_level.get("ok"):
        sea_items.append(
            {
                "text": (
                    f"Tide gauge {sea_level.get('station')}: "
                    f"{sea_level.get('latest_mm', 'n/a'):.0f} mm as of "
                    f"{sea_level.get('last_date', 'n/a')}."
                ),
                "evidence_type": "observed",
                "source": "UHSLC",
            }
        )
    sections.append({"title": "Sea level", "items": sea_items or _missing("tide gauge")})

    marine_items = []
    if marine and marine.get("ok"):
        c = marine["current"]
        marine_items.append(
            {
                "text": (
                    f"Significant wave height {c.get('wave_height_m', 'n/a')} m, "
                    f"sea-surface temperature {c.get('sst_c', 'n/a')} °C."
                ),
                "evidence_type": "observed",
                "source": "Open-Meteo marine",
            }
        )
    sections.append({"title": "Marine conditions", "items": marine_items or _missing("marine")})

    compound_items = [
        {"text": f, "evidence_type": "analyst", "source": "compound-hazard flags"} for f in compound
    ] or [
        {
            "text": "No compound drought/marine hazard flags active.",
            "evidence_type": "analyst",
            "source": "compound-hazard flags",
        }
    ]
    sections.append({"title": "Compound hazards", "items": compound_items})

    return sections


def _missing(what: str) -> list[dict[str, Any]]:
    return [{"text": f"{what} unavailable.", "evidence_type": "analyst", "source": "n/a"}]
