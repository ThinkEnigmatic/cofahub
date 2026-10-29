"""Minimal stdlib tile server for offline basemap tiles.

Serves ``data/tiles/{z}/{x}/{y}.png`` (OpenStreetMap XYZ scheme) on a loopback
port so the folium map can render offline. Run it alongside Streamlit:

    uv run python -m cofa_forward.tileserver            # port 8502 (default)
    COFA_TILE_PORT=8600 uv run python -m cofa_forward.tileserver

Env: ``COFA_TILE_DIR`` (default ``data/tiles``), ``COFA_TILE_PORT`` (default 8502).
"""

from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def _tile_root() -> Path:
    return Path(os.environ.get("COFA_TILE_DIR", "data/tiles"))


def _port() -> int:
    return int(os.environ.get("COFA_TILE_PORT", "8502"))


class TileHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        root = _tile_root()
        # Accept both /z/x/y.png and /tiles/z/x/y.png.
        rel = self.path.lstrip("/")
        if rel.startswith("tiles/"):
            rel = rel[len("tiles/") :]
        candidate = (root / rel).resolve()
        # Confine to the tile root (no path traversal).
        if not str(candidate).startswith(str(root.resolve())) or not candidate.is_file():
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Cache-Control", "public, max-age=86400")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(candidate.read_bytes())

    def log_message(self, *args) -> None:  # noqa: D401 - quiet
        pass


def serve() -> None:
    root = _tile_root()
    root.mkdir(parents=True, exist_ok=True)
    port = _port()
    server = ThreadingHTTPServer(("127.0.0.1", port), TileHandler)
    print(f"Serving offline tiles from {root} on http://127.0.0.1:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    serve()
