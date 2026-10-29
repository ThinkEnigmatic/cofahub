#!/usr/bin/env python
"""Daily refresh — push fresh data into ingestion and analysis.

Runs once per 24 hours (launchd ``com.ben.cofahub-refresh``) and:

1. re-fetches the ERA5 daily climate for every station (refreshing the 7-day
   parquet cache that feeds the drought monitor + water balance),
2. rebuilds the RAG knowledge index (docs + national plans + data-source
   catalog + geography) so retrieval stays in sync with the code,
3. refreshes the other live sources through their adapters (ENSO, marine, tide
   gauges) so their file caches are warm.

Everything is best-effort and logged; a single source failing never aborts the
rest. Run manually with:  uv run python scripts/refresh_daily.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.config import get_config  # noqa: E402
from cofa_forward.geography.registry import GeographyRegistry  # noqa: E402


def _refresh_era5(registry: GeographyRegistry) -> None:
    from cofa_forward.api import _long_era5

    print("==> refreshing ERA5 climate for all stations…")
    for e in registry.all():
        if e.entity_type == "country":
            continue
        try:
            df = _long_era5(e.latitude, e.longitude, force=True)
            print(f"  {e.geo_id}: {len(df)} days")
        except Exception as exc:  # noqa: BLE001
            print(f"  {e.geo_id}: FAILED ({exc})")


def _refresh_sources() -> None:
    from cofa_forward.ingestion.enso import CpcOniAdapter
    from cofa_forward.ingestion.marine import MarineAdapter
    from cofa_forward.ingestion.uhslc import FAS_GAUGES, UhslcAdapter
    from cofa_forward.storage.cache import FileCache

    cfg = get_config()
    cfg.ensure_data_dirs()
    cache = FileCache(cfg.data_dir("cache"), cfg.cache_ttl_seconds)

    print("==> refreshing live sources…")
    try:
        r = CpcOniAdapter(cache=cache).get_oni()
        print(f"  ENSO: {'ok' if r.get('ok') else r.get('error')}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ENSO: FAILED ({exc})")

    marine = MarineAdapter(cache=cache)
    for gauge in FAS_GAUGES.values():
        try:
            UhslcAdapter(cache=cache).get_latest(gauge)
            print(f"  tide {gauge}: ok")
        except Exception as exc:  # noqa: BLE001
            print(f"  tide {gauge}: FAILED ({exc})")
    try:
        # A representative marine refresh (the per-station values are cached on demand).
        marine.get_marine(7.116, 171.185)
        print("  marine: ok")
    except Exception as exc:  # noqa: BLE001
        print(f"  marine: FAILED ({exc})")


def _rebuild_rag() -> None:
    from cofa_forward.intelligence.rag import build_chunks, save_chunks

    print("==> rebuilding RAG index…")
    chunks = build_chunks()
    path = save_chunks(chunks)
    print(f"  {len(chunks)} chunks → {path}")


def main() -> int:
    started = time.time()
    cfg = get_config()
    registry = GeographyRegistry(cfg.geography_entities())

    _refresh_era5(registry)
    _rebuild_rag()
    _refresh_sources()

    print(f"✅ daily refresh complete in {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
