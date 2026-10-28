"""CPC Oceanic Niño Index (ONI) adapter — authoritative ENSO state.

The ONI is the canonical ENSO index (3-month running mean Niño-3.4 SST anomaly).
This adapter reads the official CPC data file and derives a phase label using the
CPC criterion (≥ +0.5 / ≤ −0.5 for ≥5 consecutive overlapping seasons). The phase
is clearly labeled *derived* — the official ENSO status statement remains the CPC
Diagnostic Discussion, which is not parsed here.
"""

from __future__ import annotations

import pandas as pd

from .base import BaseAdapter

_SEASON_MONTH = {
    "DJF": 1,
    "JFM": 2,
    "FMA": 3,
    "MAM": 4,
    "AMJ": 5,
    "MJJ": 6,
    "JJA": 7,
    "JAS": 8,
    "ASO": 9,
    "SON": 10,
    "OND": 11,
    "NDJ": 12,
}


def parse_oni(text: str) -> pd.DataFrame:
    """Parse the CPC ONI ASCII file into a DataFrame.

    Columns: ``season``, ``year``, ``month``, ``total`` (SST °C), ``anom``
    (ONI anomaly °C), ``date`` (first day of the season's center month).
    """
    rows: list[dict] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        seas = parts[0]
        if seas not in _SEASON_MONTH:
            continue
        try:
            year = int(parts[1])
            total = float(parts[2])
            anom = float(parts[3])
        except ValueError:
            continue
        rows.append(
            {
                "season": seas,
                "year": year,
                "month": _SEASON_MONTH[seas],
                "total": total,
                "anom": anom,
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(
            df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01"
        )
    return df


def classify_oni(
    df: pd.DataFrame,
    el_nino: float = 0.5,
    la_nina: float = -0.5,
    persistence: int = 5,
) -> dict:
    """Derive a phase from the ONI series using the CPC persistence criterion.

    Returns ``phase`` ("el_nino"/"la_nina"/"neutral") and ``persistence`` (the
    number of consecutive qualifying seasons ending at the latest value).
    """
    if df.empty:
        return {"phase": "neutral", "persistence": 0}
    anoms = df["anom"].tolist()

    def consecutive(pred) -> int:
        n = 0
        for a in reversed(anoms):
            if pred(a):
                n += 1
            else:
                break
        return n

    el = consecutive(lambda a: a >= el_nino)
    if el >= persistence:
        return {"phase": "el_nino", "persistence": el}
    la = consecutive(lambda a: a <= la_nina)
    if la >= persistence:
        return {"phase": "la_nina", "persistence": la}
    return {"phase": "neutral", "persistence": max(el, la)}


class CpcOniAdapter(BaseAdapter):
    source_id = "noaa-cpc-enso"
    source_url = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 30.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def get_oni(self) -> dict:
        """Fetch and parse the ONI. Never raises on network/parse errors."""
        res = self.fetch_text(self.source_url)
        if not res.ok:
            return {
                "ok": False,
                "error": res.error,
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        try:
            df = parse_oni(res.data)
        except Exception as exc:  # noqa: BLE001 - surface parse errors, don't crash
            return {
                "ok": False,
                "error": f"parse failed: {exc}",
                "source": self.source_id,
                "retrieved_at": res.retrieved_at,
            }
        if df.empty:
            return {"ok": False, "error": "no data parsed", "source": self.source_id}

        classification = classify_oni(df)
        latest = df.iloc[-1]
        return {
            "ok": True,
            "source": self.source_id,
            "source_url": self.source_url,
            "retrieved_at": res.retrieved_at,
            "from_cache": res.from_cache,
            "series": df,
            "latest": {
                "season": str(latest["season"]),
                "year": int(latest["year"]),
                "anom": float(latest["anom"]),
                "date": str(latest["date"].date()),
            },
            "phase": classification["phase"],
            "persistence_seasons": classification["persistence"],
            "note": (
                "Phase derived from the ONI threshold criterion (≥5 consecutive overlapping "
                "seasons). The ONI is the official CPC index; the authoritative ENSO status "
                "statement is the CPC Diagnostic Discussion, not parsed here."
            ),
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "retrieved_at": res.retrieved_at,
                "calculation_method": "ONI threshold classification (CPC criterion)",
                "parameters": {"el_nino": 0.5, "la_nina": -0.5, "persistence": 5},
            },
        }

    def check_availability(self):
        return {"source_id": self.source_id, "available": True, "note": "live CPC ONI"}
