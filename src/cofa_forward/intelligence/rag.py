"""COFAHUB knowledge base — retrieval over the project's own documents and data.

A dependency-free RAG retrieval layer: it chunks the project's documentation,
national drought plans, data-source catalog, and geography notes, and retrieves
the most relevant chunks for a query with BM25 (keyword relevance — explainable,
offline, deterministic). Semantic embeddings can be layered on later; BM25 is the
honest, auditable baseline.

Every chunk carries its ``source`` and ``title`` so a retrieved answer can always
point back to where it came from — the app never presents retrieval as a fact it
did not surface.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DOCS_DIR = _PROJECT_ROOT / "docs"

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


# ------------------------------------------------------------------------- #
# Chunking
# ------------------------------------------------------------------------- #
def _split_markdown(path: Path) -> list[dict[str, Any]]:
    """Split a markdown file into heading-scoped chunks."""
    text = path.read_text(encoding="utf-8", errors="replace")
    title = path.stem.replace("-", " ").title()
    chunks: list[dict[str, Any]] = []
    current_heading = "Overview"
    current: list[str] = []

    def flush() -> None:
        body = "\n".join(current).strip()
        if body:
            chunks.append(
                {
                    "title": f"{title} — {current_heading}",
                    "source": f"docs/{path.name}",
                    "kind": "doc",
                    "text": body,
                }
            )
        current.clear()

    for line in text.splitlines():
        if line.startswith("#"):
            flush()
            current_heading = line.lstrip("#").strip()
        else:
            current.append(line)
    flush()
    return chunks


def _chunk_plans() -> list[dict[str, Any]]:
    from .guidance.national_plans import NATIONAL_PLANS

    chunks = []
    for p in NATIONAL_PLANS:
        text = f"{p['title']}. {p['summary']} " + " ".join(p["key_facts"])
        chunks.append(
            {
                "title": p["title"],
                "source": p["url"],
                "kind": "plan",
                "text": text,
            }
        )
    return chunks


def _chunk_sources() -> list[dict[str, Any]]:
    from .config import get_config

    chunks = []
    for s in get_config().sources():
        text = (
            f"{s.name}. Publisher {s.publisher}. {s.geographic_coverage or ''} "
            f"{s.variables or ''} {s.notes or ''}"
        )
        chunks.append(
            {
                "title": s.name,
                "source": s.url or s.id,
                "kind": "source",
                "text": text,
            }
        )
    return chunks


def _chunk_geography() -> list[dict[str, Any]]:
    from .config import get_config

    chunks = []
    for e in get_config().geography_entities():
        text = f"{e.name} ({e.geo_id}) — {e.entity_type} in {e.country_code}. {e.notes or ''}"
        chunks.append(
            {
                "title": f"{e.name} ({e.geo_id})",
                "source": "config/geography.yaml",
                "kind": "geography",
                "text": text,
            }
        )
    return chunks


def build_chunks() -> list[dict[str, Any]]:
    """Assemble all knowledge chunks (docs + plans + sources + geography)."""
    chunks: list[dict[str, Any]] = []
    if _DOCS_DIR.exists():
        for md in sorted(_DOCS_DIR.glob("*.md")):
            chunks.extend(_split_markdown(md))
    chunks.extend(_chunk_plans())
    chunks.extend(_chunk_sources())
    chunks.extend(_chunk_geography())
    return chunks


# ------------------------------------------------------------------------- #
# BM25 retrieval
# ------------------------------------------------------------------------- #
class KnowledgeBase:
    """A BM25 index over the knowledge chunks."""

    def __init__(self, chunks: list[dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.corpus = [tokenize(c["text"]) for c in chunks]
        self.doc_len = [len(d) for d in self.corpus]
        self.n = len(self.corpus)
        self.avgdl = sum(self.doc_len) / max(1, self.n)
        self.k1, self.b = k1, b
        self.df: Counter[str] = Counter()
        for doc in self.corpus:
            for term in set(doc):
                self.df[term] += 1

    def _idf(self, term: str) -> float:
        n_term = self.df.get(term, 0)
        if n_term == 0:
            return 0.0
        return math.log(1.0 + (self.n - n_term + 0.5) / (n_term + 0.5))

    def _score(self, query_terms: list[str], doc_idx: int) -> float:
        doc = self.corpus[doc_idx]
        tf = Counter(doc)
        dl = self.doc_len[doc_idx]
        score = 0.0
        for term in set(query_terms):
            idf = self._idf(term)
            if idf == 0.0:
                continue
            f = tf.get(term, 0)
            if f == 0:
                continue
            denom = f + self.k1 * (1.0 - self.b + self.b * dl / self.avgdl)
            score += idf * (f * (self.k1 + 1.0)) / denom
        return score

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        terms = tokenize(query)
        if not terms:
            return []
        scored = sorted(
            ((self._score(terms, i), i) for i in range(self.n)),
            key=lambda x: x[0],
            reverse=True,
        )
        return [
            {**self.chunks[i], "score": round(s, 4)}
            for s, i in scored[:top_k]
            if s > 0
        ]


# ------------------------------------------------------------------------- #
# Persistence (chunks are cheap to re-index; only the chunks are stored)
# ------------------------------------------------------------------------- #
def default_index_path() -> Path:
    return _PROJECT_ROOT / "data" / "rag" / "chunks.json"


def save_chunks(chunks: list[dict[str, Any]], path: Path | None = None) -> Path:
    path = path or default_index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(chunks, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def load_chunks(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or default_index_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []


def load_knowledge_base(path: Path | None = None) -> KnowledgeBase:
    """Load the persisted chunks (rebuilding the BM25 index in memory)."""
    return KnowledgeBase(load_chunks(path))
