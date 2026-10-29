"""Prefetch all live sources into an offline snapshot.

Run while online; the result lets the app run without a network connection
(``COFA_OFFLINE=1``). The script:

1. warms the file cache + downloads raw rasters (WorldPop, boundaries, NMME,
   IBTrACS) by calling the same adapters the UI uses, and
2. writes structured per-source JSON/Parquet into ``data/snapshot/`` with a
   ``manifest.json`` (CHIRPS monthly series per location, Himawari imagery, and
   the text/JSON products).

Nothing is fabricated: a source that fails to fetch is recorded as missing in the
manifest and reported in the summary.

Usage:
    uv run python scripts/prefetch_snapshot.py [--locations PAL-KOR,RMI-MAJ] [--skip-ibtracs]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.config import get_config  # noqa: E402
from cofa_forward.storage.cache import FileCache  # noqa: E402
from cofa_forward.storage.snapshot import SnapshotStore, snapshot_dir  # noqa: E402


def _cache(cfg) -> FileCache:
    cfg.ensure_data_dirs()
    # Long TTL so the warmed cache persists as the offline store.
    return FileCache(cfg.data_dir("cache"), cfg.cache_ttl_seconds, serve_stale=True)


def _fetch_global(store: SnapshotStore, cache: FileCache) -> None:
    """Fetch the non-location-specific sources into the snapshot."""
    from cofa_forward.ingestion.enso import CpcOniAdapter
    from cofa_forward.ingestion.enso_discussion import CpcEnsoDiscussionAdapter
    from cofa_forward.ingestion.jma import JmaTyphoonAdapter
    from cofa_forward.ingestion.jtwc import JtwcAdapter
    from cofa_forward.ingestion.nws_guam import NwsGuamAdapter
    from cofa_forward.ingestion.peac import PeacRainfallOutlookAdapter

    sources = [
        ("enso_oni", lambda: CpcOniAdapter(cache=cache).get_oni()),
        ("enso_discussion", lambda: CpcEnsoDiscussionAdapter(cache=cache).get_discussion()),
        ("jma_active", lambda: JmaTyphoonAdapter(cache=cache).active_storms()),
        ("jtwc_warnings", lambda: JtwcAdapter(cache=cache).get_active_warnings()),
        ("nws_guam", lambda: NwsGuamAdapter(cache=cache).get_advisory()),
        ("peac_outlook", lambda: PeacRainfallOutlookAdapter(cache=cache).get_outlook()),
    ]
    for source_id, fetch in sources:
        try:
            r = fetch()
            if r.get("ok"):
                store.write(source_id, r)
            else:
                store.mark_missing(source_id, r.get("error", "fetch failed"))
        except Exception as exc:  # noqa: BLE001
            store.mark_missing(source_id, f"{type(exc).__name__}: {exc}")


def _fetch_himawari(store: SnapshotStore) -> None:
    """Download the latest Himawari full-disk composite for offline display."""
    from cofa_forward.ingestion.himawari import full_disk_url

    url, t = full_disk_url()
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        dest = store.directory / "himawari_latest.png"
        dest.write_bytes(resp.content)
        store.write(
            "himawari_latest",
            {
                "image_path": str(dest),
                "image_url": url,
                "time": t.isoformat(),
                "resolution": "full disk, 10-min cadence (geostationary)",
            },
        )
    except Exception as exc:  # noqa: BLE001
        store.mark_missing("himawari_latest", f"{type(exc).__name__}: {exc}")


def _fetch_ibtracs(cache: FileCache) -> None:
    from cofa_forward.ingestion.ibtracs import FAS_BBOX, IbtracsAdapter

    try:
        r = IbtracsAdapter(cache=cache).get_tracks(bbox=FAS_BBOX)
        if not r.get("ok"):
            print(f"  ibtracs: {r.get('error')}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ibtracs: {type(exc).__name__}: {exc}")


def _fetch_location(store: SnapshotStore, cache: FileCache, cfg, entity) -> None:
    """Fetch per-location sources: forecast, ERA5 archive, CHIRPS, WorldPop, NMME."""
    from cofa_forward.ingestion.boundaries import BoundariesAdapter, match_by_name, zonal_population
    from cofa_forward.ingestion.chirps import ChirpsAdapter
    from cofa_forward.ingestion.nmme import NmmeAdapter
    from cofa_forward.ingestion.population import WorldPopAdapter
    from cofa_forward.ingestion.rainfall import OpenMeteoArchiveAdapter
    from cofa_forward.ingestion.weather import OpenMeteoForecastAdapter

    lat, lon = entity.latitude, entity.longitude

    # Forecast (Open-Meteo).
    try:
        r = OpenMeteoForecastAdapter(config=cfg, cache=cache).get_forecast(lat, lon)
        store.write(f"forecast_{entity.geo_id}", r if r.get("ok") else {"error": r.get("error")})
    except Exception as exc:  # noqa: BLE001
        store.mark_missing(f"forecast_{entity.geo_id}", str(exc))

    # ERA5 daily archive (1997→now), in ~10-year chunks.
    try:
        adapter = OpenMeteoArchiveAdapter(config=cfg, cache=cache)
        import pandas as pd

        today = pd.Timestamp.today(tz="UTC").strftime("%Y-%m-%d")
        parts = []
        for start, end in (
            ("1997-01-01", "2006-12-31"),
            ("2007-01-01", "2016-12-31"),
            ("2017-01-01", today),
        ):
            rr = adapter.get_rainfall(lat, lon, start, end)
            if rr.get("ok"):
                parts.append(rr["series"])
        if parts:
            series = pd.concat(parts)
            series = series[~series.index.duplicated(keep="last")].sort_index()
            store.write_df(
                f"rainfall_{entity.geo_id}",
                series.rename("precip_mm").reset_index(),
            )
        else:
            store.mark_missing(f"rainfall_{entity.geo_id}", "no ERA5 series")
    except Exception as exc:  # noqa: BLE001
        store.mark_missing(f"rainfall_{entity.geo_id}", str(exc))

    # CHIRPS monthly (land-masked; extract once and cache locally).
    try:
        series = ChirpsAdapter(cache=cache).get_monthly_series(
            lat, lon, "1991-01-01", "2024-12-31"
        )["series"]
        store.write_df(f"chirps_monthly_{entity.geo_id}", series.rename("precip_mm").reset_index())
    except Exception as exc:  # noqa: BLE001
        store.mark_missing(f"chirps_monthly_{entity.geo_id}", str(exc))

    # WorldPop point/radius + zonal population.
    try:
        wpa = WorldPopAdapter(config=cfg)
        iso3 = WorldPopAdapter.iso3(entity.country_code)
        radius_pop = wpa.population_within_radius(entity.country_code, lat, lon, 10.0)
        zonal = None
        if entity.country_code.upper() in ("FM", "MH", "PW"):
            rec = match_by_name(entity.name, BoundariesAdapter(config=cfg).get_admin(iso3, level=1))
            if rec is not None:
                zonal = zonal_population(rec["geometry"], wpa.raster_path(iso3))
        store.write(
            f"population_{entity.geo_id}",
            {"radius_km": 10.0, "radius_population": radius_pop, "zonal_population": zonal},
        )
    except Exception as exc:  # noqa: BLE001
        store.mark_missing(f"population_{entity.geo_id}", str(exc))

    # NMME seasonal forecast (downloads NetCDF to data/raw/nmme, reused offline).
    try:
        r = NmmeAdapter(config=cfg).get_multimodel(lat, lon, variable="prate")
        if r.get("ok"):
            store.write(
                f"nmme_{entity.geo_id}",
                {
                    "cycle": r.get("cycle"),
                    "n_models": r.get("n_models"),
                    "ensemble_mean": list(r["ensemble_mean"].values),
                    "lead_months": list(r["ensemble_mean"].index.astype(str)),
                },
            )
        else:
            store.mark_missing(f"nmme_{entity.geo_id}", r.get("error", "no NMME"))
    except Exception as exc:  # noqa: BLE001
        store.mark_missing(f"nmme_{entity.geo_id}", str(exc))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--locations", help="comma-separated geo_ids (default: all)")
    parser.add_argument(
        "--skip-ibtracs", action="store_true", help="skip the 114 MB IBTrACS download"
    )
    args = parser.parse_args()

    cfg = get_config()
    cfg.ensure_data_dirs()
    cache = _cache(cfg)
    store = SnapshotStore(snapshot_dir(cfg))

    from cofa_forward.geography.registry import GeographyRegistry

    registry = GeographyRegistry(cfg.geography_entities())
    entities = registry.all()
    if args.locations:
        wanted = {g.strip() for g in args.locations.split(",") if g.strip()}
        entities = [e for e in entities if e.geo_id in wanted]

    print(f"Prefetching {len(entities)} location(s) + global sources → {store.directory}")

    _fetch_global(store, cache)
    _fetch_himawari(store)
    if not args.skip_ibtracs:
        _fetch_ibtracs(cache)

    for i, e in enumerate(entities, 1):
        print(f"[{i}/{len(entities)}] {e.geo_id} {e.name}")
        _fetch_location(store, cache, cfg, e)

    manifest = store.manifest()
    sources = manifest.get("sources", {})
    ok = sum(1 for v in sources.values() if v.get("ok"))
    missing = [s for s, v in sources.items() if not v.get("ok")]
    print(f"\nSnapshot: {ok} sources captured, {len(missing)} missing.")
    if missing:
        print("Missing:")
        for s in missing:
            print(f"  - {s}: {sources[s].get('reason', 'unknown')}")
    print(f"Manifest: {store.directory / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
