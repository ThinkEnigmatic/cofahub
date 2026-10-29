#!/usr/bin/env python
"""Build (or rebuild) the COFAHUB RAG index from the project's documents + data.

Chunks the docs, national plans, data-source catalog, and geography notes, then
persists them to ``data/rag/chunks.json``. Run on a schedule (see
scripts/refresh_daily.py) so the knowledge base stays in sync with the code.

Usage:  uv run python scripts/build_rag_index.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.intelligence.rag import build_chunks, save_chunks  # noqa: E402


def main() -> int:
    chunks = build_chunks()
    path = save_chunks(chunks)
    print(f"Built RAG index: {len(chunks)} chunks → {path}")
    kinds: dict[str, int] = {}
    for c in chunks:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    print("  by kind:", kinds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
