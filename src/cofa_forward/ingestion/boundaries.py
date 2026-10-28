"""Administrative boundaries adapter (HDX COD-AB).

Loads the OCHA/HDX Common Operational Dataset administrative boundaries for FSM
and RMI (Shapefile, CC BY-IGO). Palau has no COD-AB (use SPC Pacific Data Hub —
a documented follow-up), so Palau remains point-based.

Boundaries enable:
* accurate atoll/state population (zonal sum of WorldPop within the polygon),
* point-in-polygon attribution, and
* real polygon geometry (map + area).

Implemented with ``pyshp`` (pure-Python Shapefile reader) + ``rasterio`` for
rasterization — no GDAL/geopandas system dependency. Geometry uses the exterior
ring of each polygon; interior holes (rare at atoll scale) are ignored and this
simplification is documented.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import rasterio
import rasterio.features
import shapefile

from .base import BaseAdapter
from .population import NODATA

# Verified download URLs (2026-10-28). Palau: no COD-AB (documented follow-up).
COD_AB_DOWNLOADS = {
    "MHL": (
        "https://data.humdata.org/dataset/c215706c-9c22-43ca-8d36-9de4726eb9e0/"
        "resource/383a9368-998f-4657-a380-6323bb827296/download/mhl_admbnda_wgs84_ab_shp.zip",
        "mhl_admbnda_wgs84_adm{level}.shp",
    ),
    "FSM": (
        "https://data.humdata.org/dataset/dc71c13f-e848-4ddc-9074-17e608464b63/"
        "resource/7348d022-6726-438c-9b1c-0b5524b7dbfd/download/fsm_admbnda_shp.zip",
        "fsm_admbnda_adm{level}.shp",
    ),
}


_POLYGON_TYPES = (shapefile.POLYGON, shapefile.POLYGONZ, shapefile.POLYGONM)


def shape_to_geojson(shp) -> dict | None:
    """Convert a pyshp shape to a GeoJSON geometry dict.

    Accepts POLYGON / POLYGONZ / POLYGONM. Multi-part shapes (e.g. multi-island
    states) become a MultiPolygon; single-part become a Polygon. Z/M ordinates
    are dropped. Interior holes (rare at atoll scale) are treated as separate
    parts — a documented simplification.
    """
    if shp.shapeType not in _POLYGON_TYPES:
        return None
    if not shp.points:
        return None
    parts = []
    for i, start in enumerate(shp.parts):
        end = shp.parts[i + 1] if i + 1 < len(shp.parts) else len(shp.points)
        parts.append([[float(p[0]), float(p[1])] for p in shp.points[start:end]])
    if len(parts) == 1:
        return {"type": "Polygon", "coordinates": parts}
    # MultiPolygon: each part is a polygon, itself a list of (one) ring.
    return {"type": "MultiPolygon", "coordinates": [[ring] for ring in parts]}


def parse_admin_shp(shp_path: str, level: int) -> list[dict]:
    """Parse an administrative Shapefile into ``{name, pcode, geometry}`` records.

    Handles the two common COD-AB field conventions (``ADM{level}_EN`` and
    ``ADM{level}NAME``/``ADM{level}_NAME``).
    """
    sf = shapefile.Reader(shp_path)
    fields = [f[0] for f in sf.fields[1:]]
    name_field = next(
        (c for c in (f"ADM{level}_EN", f"ADM{level}NAME", f"ADM{level}_NAME") if c in fields),
        None,
    )
    pcode_field = next((c for c in (f"ADM{level}_PCODE", f"ADM{level}PCODE") if c in fields), None)
    out = []
    for sr in sf.shapeRecords():
        rec = dict(zip(fields, sr.record, strict=True))
        geom = shape_to_geojson(sr.shape)
        if geom is None:
            continue
        out.append(
            {
                "name": rec.get(name_field) if name_field else None,
                "pcode": rec.get(pcode_field) if pcode_field else None,
                "level": level,
                "geometry": geom,
            }
        )
    return out


def zonal_population(geometry: dict, worldpop_path: str) -> float:
    """Sum WorldPop population (UN-adjusted) within a GeoJSON geometry."""
    with rasterio.open(worldpop_path) as ds:
        mask = rasterio.features.rasterize(
            [(geometry, 1)],
            out_shape=(ds.height, ds.width),
            transform=ds.transform,
            fill=0,
            dtype="uint8",
        )
        data = ds.read(1)
        valid = data > NODATA
        sel = (mask == 1) & valid
        return float(data[sel].sum())


def match_by_name(name: str, records: list[dict]) -> dict | None:
    """Return the admin record whose name matches (case-insensitive, exact)."""
    target = (name or "").strip().lower()
    for r in records:
        if r.get("name") and r["name"].strip().lower() == target:
            return r
    return None


class BoundariesAdapter(BaseAdapter):
    source_id = "hdx-cod-ab"
    source_url = "https://data.humdata.org/dataset/cod-ab-fsm"
    implementation_status = "implemented_and_tested"

    def __init__(self, config=None, cache=None, db=None, timeout: float = 60.0):
        super().__init__(cache=cache, db=db, timeout=timeout)
        self.raw_dir = (
            Path(config.data_dir("raw")) / "boundaries" if config else Path("data/raw/boundaries")
        )

    def admin_path(self, iso3: str, level: int) -> str:
        """Download (once) and return the local path to an admin SHP file."""
        iso3 = iso3.upper()
        if iso3 not in COD_AB_DOWNLOADS:
            raise ValueError(f"No COD-AB boundaries configured for {iso3}")
        url, pattern = COD_AB_DOWNLOADS[iso3]
        rel = pattern.format(level=level)
        dest = self.raw_dir / iso3.lower() / rel
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            zip_path = self.raw_dir / f"{iso3.lower()}_admbnda_shp.zip"
            if not zip_path.exists():
                resp = self.session.get(url, stream=True, timeout=self.timeout)
                resp.raise_for_status()
                with open(zip_path, "wb") as fh:
                    for chunk in resp.iter_content(256 * 1024):
                        fh.write(chunk)
            with zipfile.ZipFile(zip_path) as zf:
                zf.extract(rel, dest.parent)
        return str(dest)

    def get_admin(self, iso3: str, level: int = 1) -> list[dict]:
        """Return the parsed admin records (name, pcode, geometry) for a level."""
        return parse_admin_shp(self.admin_path(iso3, level), level)

    def check_availability(self):
        return {"source_id": self.source_id, "available": True, "note": "HDX COD-AB (FSM/RMI)"}
