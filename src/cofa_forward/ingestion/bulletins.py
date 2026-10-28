"""Bulletin / advisory monitor.

Many authoritative sources publish regular public bulletins rather than stable
APIs. This monitor polls configured bulletin sources, detects new or updated
content (by content hash), parses a structured summary, stores a raw snapshot,
and records each update — so alerts and updates flow into the dataset dynamically.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

from ..config import Config
from ..storage.cache import FileCache
from ..storage.database import Database
from .base import BaseAdapter


class _BulletinFetcher(BaseAdapter):
    source_id = "bulletins"


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #


def parse_wmo_text(text: str) -> dict[str, Any]:
    """Parse an NWS/JTWC text product: header, agency, issue time, headline."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    header = agency = issue_time = None
    if lines:
        parts = lines[0].split()
        if parts:
            header = parts[0]
        if len(parts) > 1:
            agency = parts[1]
        if len(parts) > 2:
            issue_time = parts[2]
    headline = None
    # Prefer a specific hazard keyword over the generic "BULLETIN" banner.
    for keyword in ("ADVISORY", "WARNING", "STATEMENT", "WATCH", "UPDATE"):
        for ln in lines[1:]:
            if keyword in ln.upper():
                headline = ln
                break
        if headline:
            break
    if headline is None:
        for ln in lines[1:]:
            if "BULLETIN" in ln.upper():
                headline = ln
                break
    if headline is None and len(lines) > 1:
        headline = lines[1]
    return {
        "header": header,
        "agency": agency,
        "issue_time": issue_time,
        "headline": headline,
    }


def parse_jma_info(data: Any) -> dict[str, Any]:
    """Summarize the JMA typhoon-information JSON bulletin list."""
    items = data or []
    if not items:
        return {"n_bulletins": 0, "latest": None}
    latest = max(items, key=lambda it: str(it.get("datetime") or ""))
    return {
        "n_bulletins": len(items),
        "latest_headline": latest.get("headTitle"),
        "latest_datetime": latest.get("reportDatetime") or latest.get("datetime"),
        "latest_event_id": latest.get("eventId"),
        "latest_info_type": latest.get("infoType"),
        "latest_header": latest.get("header"),
    }


_ENSO_STATUSES = (
    "El Niño Advisory",
    "La Niña Advisory",
    "El Niño Watch",
    "La Niña Watch",
    "Final El Niño Advisory",
    "Final La Niña Advisory",
    "ENSO-neutral",
    "Not Active",
)


def parse_cpc_enso_html(html_text: str) -> dict[str, Any]:
    """Extract the ENSO alert status + last-modified date from the CPC HTML.

    Tags are stripped and HTML entities unescaped so the status is captured even
    when split across markup (e.g. ``El Ni&ntilde;o Advisory``).
    """
    text = re.sub(r"<[^>]+>", " ", html_text or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    status = None
    m = re.search(r"ENSO Alert System Status:\s*(.*?)\s*Synopsis", text, re.IGNORECASE)
    if m:
        status = m.group(1).strip()
    if not status:
        for s in _ENSO_STATUSES:
            if s in text:
                status = s
                break

    m2 = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", text)
    return {
        "enso_alert_status": status,
        "last_modified": m2.group(1) if m2 else None,
    }


def summarize(kind: str, data: Any) -> dict[str, Any]:
    """Dispatch to the appropriate parser and return a structured summary."""
    if kind == "wmo_text":
        return parse_wmo_text(data or "")
    if kind == "jma_info":
        return parse_jma_info(data)
    if kind == "cpc_enso_html":
        return parse_cpc_enso_html(data or "")
    return {"note": f"no parser for kind {kind!r}"}


# --------------------------------------------------------------------------- #
# Monitor
# --------------------------------------------------------------------------- #
class BulletinMonitor:
    """Poll bulletin sources and record updates."""

    def __init__(self, config: Config, cache: FileCache | None = None, db: Database | None = None):
        self.config = config
        self.fetcher = _BulletinFetcher(cache=cache, db=db)
        self.db = db
        self.raw_dir = config.data_dir("raw") / "bulletins"

    def _content(self, kind: str, data: Any) -> str:
        if isinstance(data, str):
            return data
        return json.dumps(data, sort_keys=True, default=str)

    def _fetch(self, source: dict[str, Any]):
        url = source["url"]
        kind = source.get("kind", "wmo_text")
        if kind in ("wmo_text", "cpc_enso_html"):
            return self.fetcher.fetch_text(url)
        return self.fetcher.fetch_json(url)

    def check(self, source: dict[str, Any]) -> dict[str, Any]:
        """Check one source; returns an update dict (``changed`` True if new)."""
        res = self._fetch(source)
        if not res.ok:
            return {
                "source_id": source["id"],
                "name": source["name"],
                "ok": False,
                "error": res.error,
                "changed": False,
            }

        content = self._content(source.get("kind", "wmo_text"), res.data)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        summary = summarize(source.get("kind", "wmo_text"), res.data)
        summary_text = json.dumps(summary, ensure_ascii=False, default=str)

        prev_hash = self.db.get_bulletin_hash(source["id"]) if self.db else None
        changed = prev_hash != digest

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = str(self.raw_dir / f"{source['id']}_{digest[:12]}.txt")
        Path(raw_path).write_text(content, encoding="utf-8")

        if self.db:
            self.db.upsert_bulletin(
                source["id"], source["name"], res.retrieved_at, digest, summary_text, raw_path
            )
            if changed:
                self.db.insert_bulletin_update(
                    source["id"], source["name"], res.retrieved_at, digest, summary_text, raw_path
                )

        return {
            "source_id": source["id"],
            "name": source["name"],
            "ok": True,
            "changed": changed,
            "retrieved_at": res.retrieved_at,
            "content_hash": digest[:12],
            "summary": summary,
        }

    def check_all(self) -> list[dict[str, Any]]:
        """Check every configured source and return the list of updates."""
        updates = []
        for source in self.config.bulletin_sources():
            result = self.check(source)
            if result.get("changed"):
                updates.append(result)
        return updates
