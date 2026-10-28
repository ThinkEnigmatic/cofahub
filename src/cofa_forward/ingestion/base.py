"""Base data-ingestion adapter.

Every provider adapter implements a consistent interface: check availability,
fetch (with retries/backoff/timeout), validate, normalize, record provenance,
and report failures. One provider failing must never crash the application.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import requests

from ..storage.cache import FileCache, cache_key
from ..storage.database import Database
from ..timeutil import format_iso, now_utc

logger = logging.getLogger("cofa_forward.ingestion")


@dataclass
class FetchResult:
    ok: bool
    source_id: str
    source_url: str
    data: Any = None
    error: str | None = None
    retrieved_at: str = field(default_factory=lambda: format_iso(now_utc()))
    from_cache: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "error": self.error,
            "retrieved_at": self.retrieved_at,
            "from_cache": self.from_cache,
        }


class BaseAdapter:
    """Shared fetch/validate/provenance plumbing for provider adapters."""

    source_id = "base"
    source_url = ""

    def __init__(
        self,
        cache: FileCache | None = None,
        db: Database | None = None,
        timeout: float = 20.0,
        retries: int = 3,
        backoff: float = 1.0,
    ):
        self.cache = cache
        self.db = db
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.session = requests.Session()

    # ------------------------------------------------------------------ #
    def _request(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> tuple[bool, str, str | None, str, bool]:
        """Fetch the raw text of a URL with retry/backoff/timeout and caching.

        Returns ``(ok, text, error, retrieved_at, from_cache)``.
        """
        params = params or {}
        key = cache_key(url, params)
        if self.cache is not None:
            cached = self.cache.get(key)
            if cached is not None:
                return True, cached.decode("utf-8"), None, format_iso(now_utc()), True

        timeout = timeout or self.timeout
        last_err: str | None = None
        for attempt in range(self.retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=timeout)
                if resp.status_code == 429:
                    last_err = "rate-limited (HTTP 429)"
                elif resp.status_code >= 500:
                    last_err = f"server error (HTTP {resp.status_code})"
                elif resp.status_code >= 400:
                    last_err = f"HTTP {resp.status_code}"
                    break  # do not retry client errors
                else:
                    resp.raise_for_status()
                    text = resp.text
                    if self.cache is not None:
                        self.cache.set(key, text.encode("utf-8"))
                    if self.db is not None:
                        self.db.record_ingestion(
                            self.source_id, "ok", retrieved_at=format_iso(now_utc())
                        )
                    return True, text, None, format_iso(now_utc()), False
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_err = f"network error: {exc.__class__.__name__}"
            except requests.HTTPError as exc:
                last_err = f"HTTP error: {exc}"
                break

            if attempt < self.retries:
                sleep = self.backoff * (2**attempt)
                logger.warning(
                    "%s fetch attempt %d failed (%s); retrying in %.1fs",
                    self.source_id,
                    attempt + 1,
                    last_err,
                    sleep,
                )
                time.sleep(sleep)

        if self.db is not None:
            self.db.record_ingestion(
                self.source_id, "error", last_err or "unknown", retrieved_at=format_iso(now_utc())
            )
        return False, "", last_err, format_iso(now_utc()), False

    def fetch_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> FetchResult:
        """Fetch and parse JSON with retry/backoff/timeout and caching."""
        ok, text, err, retrieved_at, from_cache = self._request(url, params, timeout)
        if not ok:
            return FetchResult(False, self.source_id, url, error=err, retrieved_at=retrieved_at)
        try:
            data = json.loads(text)
        except ValueError as exc:
            return FetchResult(
                False, self.source_id, url, error=f"invalid JSON: {exc}", retrieved_at=retrieved_at
            )
        return FetchResult(
            True, self.source_id, url, data=data, retrieved_at=retrieved_at, from_cache=from_cache
        )

    def fetch_text(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> FetchResult:
        """Fetch raw text with retry/backoff/timeout and caching."""
        ok, text, err, retrieved_at, from_cache = self._request(url, params, timeout)
        if not ok:
            return FetchResult(False, self.source_id, url, error=err, retrieved_at=retrieved_at)
        return FetchResult(
            True, self.source_id, url, data=text, retrieved_at=retrieved_at, from_cache=from_cache
        )

    # ------------------------------------------------------------------ #
    def check_availability(self) -> dict[str, Any]:
        """Lightweight availability probe. Subclasses may override."""
        return {"source_id": self.source_id, "available": True, "note": "adapter configured"}

    @staticmethod
    def validate_not_empty(data: Any, context: str) -> None:
        if data is None:
            raise ValueError(f"{context}: empty response")
