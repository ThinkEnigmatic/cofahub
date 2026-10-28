"""JMA Himawari-9 geostationary satellite imagery (NICT real-time web).

Himawari-9 provides full-disk visible/infrared imagery of the western Pacific
every 10 minutes. The NICT real-time web serves composited tiles at
``https://himawari8.nict.go.jp/img/D531106/{level}/{width}/{date}/{time}_{x}_{y}.png``
(no band in the URL — ``1d`` is the full-disk composite). No auth required.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .base import BaseAdapter

BASE = "https://himawari8.nict.go.jp/img/D531106"


def latest_time(offset_minutes: int = 20) -> datetime:
    """Latest available imagery time (rounded down to 10-min, minus a latency)."""
    now = datetime.now(UTC) - timedelta(minutes=offset_minutes)
    minute = (now.minute // 10) * 10
    return now.replace(minute=minute, second=0, microsecond=0)


def tile_url(
    level: str = "1d", width: int = 550, t: datetime | None = None, x: int = 0, y: int = 0
) -> str:
    """Construct a Himawari tile URL."""
    t = t or latest_time()
    date = t.strftime("%Y/%m/%d")
    time = t.strftime("%H%M%S")
    return f"{BASE}/{level}/{width}/{date}/{time}_{x}_{y}.png"


def full_disk_url(width: int = 550, offset_minutes: int = 20) -> tuple[str, datetime]:
    """Latest full-disk composite image URL and its timestamp.

    The NICT full-disk composite is served at width 550 (``1d/550``); 1100 is
    not a valid width for the ``1d`` level.
    """
    t = latest_time(offset_minutes)
    return tile_url("1d", width, t, 0, 0), t


class HimawariAdapter(BaseAdapter):
    source_id = "jma-himawari"
    source_url = "https://himawari8.nict.go.jp/"
    implementation_status = "implemented_and_tested"

    def __init__(self, cache=None, db=None, timeout: float = 30.0):
        super().__init__(cache=cache, db=db, timeout=timeout)

    def latest_full_disk(self, width: int = 550) -> dict:
        """Return the latest full-disk image URL (composite) with its timestamp."""
        url, t = full_disk_url(width)
        return {
            "ok": True,
            "source": self.source_id,
            "image_url": url,
            "time": t.isoformat(),
            "resolution": "full disk, 10-min cadence (geostationary)",
            "provenance": {
                "dataset_id": self.source_id,
                "source_url": self.source_url,
                "calculation_method": "latest 10-min full-disk composite tile",
                "notes": (
                    "Himawari-9 geostationary satellite; FAS is in the western-Pacific portion."
                ),
            },
        }

    def check_availability(self):
        return {"source_id": self.source_id, "available": True, "note": "live Himawari-9 imagery"}
