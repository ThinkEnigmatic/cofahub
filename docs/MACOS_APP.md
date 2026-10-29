# COFA FORWARD — macOS app (SwiftUI shell + offline cache)

A native macOS app for the MacBook Pro that runs the full COFA FORWARD Streamlit
dashboard locally, with an offline snapshot so it works **anytime** — with or
without a network connection.

## Architecture

```
COFA Forward.app (SwiftUI, arm64, macOS 14+)
  ├─ WKWebView  ── loads http://127.0.0.1:8501
  ├─ ServerManager ── launches `.venv/bin/streamlit run …` (or `uv run streamlit`)
  │                    as a child process; sets COFA_OFFLINE=1 when toggled
  └─ "Refresh snapshot" ── runs `scripts/prefetch_snapshot.py`
```

The app is a **thin shell** — it does not reimplement any science. All 12 pages,
the Python deterministic-science layer, and the folium maps run in the bundled
Streamlit app; the Swift layer only hosts the process + web view and controls
offline mode.

## Offline cache

`COFA_OFFLINE=1` (set by the app's Offline toggle) switches the app to read the
pre-fetched snapshot instead of the network:

| Mechanism | What it covers |
|---|---|
| `FileCache(serve_stale=True)` | every adapter that goes through `make_cache()` (ENSO, ENSO discussion, JMA, JTWC, NWS Guam, PEAC, forecast, ERA5 archive) serves its cached raw responses past their TTL |
| `data/raw/` | WorldPop rasters, boundary SHP/GeoJSON, NMME NetCDF, IBTrACS CSV — downloaded once, re-read locally |
| `data/snapshot/` | structured per-source JSON/Parquet (CHIRPS monthly series per location, Himawari PNG, population, NMME) + `manifest.json` |

The snapshot is produced by `scripts/prefetch_snapshot.py` (run when online):

```bash
uv run python scripts/prefetch_snapshot.py --skip-ibtracs   # all locations
uv run python scripts/prefetch_snapshot.py --locations RMI-MAJ
```

The manifest records what was captured and when; a source that failed to fetch is
recorded as **missing** (never fabricated) and surfaced on the Data Sources page.

### Offline map tiles

`scripts/prefetch_tiles.py` downloads OpenStreetMap tiles (region z0-9 + a window
around each location at z10-11) into `data/tiles/`, and `cofa_forward.tileserver`
serves them on `127.0.0.1:8502`. In offline mode the map's "OpenStreetMap
(streets)" basemap is swapped to the local server, so the map *and* its imagery
work without a connection.

```bash
uv run python scripts/prefetch_tiles.py
uv run python -m cofa_forward.tileserver          # the macOS app starts this automatically
```

OSM is used for offline imagery because it is openly licensed (ODbL, attribution
required), permits caching for light personal use, and reaches high zoom. The
satellite basemaps (Esri/GIBS) are **not** cached offline — Esri restricts bulk
caching and GIBS true-colour caps at ~zoom 9 where atolls are only a few pixels.

## Build & deploy

```bash
# build + assemble the .app bundle (ad-hoc signed, not sandboxed)
cd apps/macos && ./package_app.sh

# deploy to the MBP (rsync source → uv sync → optional prefetch → build → /Applications)
scripts/deploy_macos_app.sh --host bens-macbook-pro.local [--snapshot]
```

## Requirements on the target (MBP)

* `uv` on PATH (at `~/.local/bin/uv`) — the app resolves it, or uses `.venv/bin/streamlit` if present.
* `~/cofa-forward` present (synced by `deploy_macos_app.sh`).
* First launch (online) runs `uv sync` once to build the venv; after that it is offline-capable.

## Honest limitations

* **Offline imagery is OpenStreetMap streets, not satellite.** The satellite
  basemaps (Esri/GIBS) still need a connection — Esri restricts bulk caching and
  GIBS true-colour caps at ~zoom 9. The offline tile cache covers OSM (region
  z0-9 + per-location z10-11) for a genuinely offline map with coastlines and
  place names, but not high-resolution satellite pictures of individual atolls.
* The offline snapshot is a **point-in-time capture**, not live data; the UI shows
  the snapshot age.
* The app is **not sandboxed** (ad-hoc signed) because it must launch a Python
  server and read `~/cofa-forward`. Do not distribute it outside this machine.
