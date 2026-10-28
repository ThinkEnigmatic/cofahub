"""Configuration loading and validation.

Loads the YAML configuration tree from ``config/`` and exposes typed access.
Startup validation ensures the app fails with a clear message on malformed
config rather than silently misbehaving.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .schemas import AlertThreshold, EnsoEpisode, GeoEntity, SourceRecord

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"


class ConfigError(RuntimeError):
    """Raised when configuration is missing or invalid."""


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config file must contain a mapping: {path}")
    return data


class Config:
    """Validated application configuration."""

    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root else PROJECT_ROOT
        self.config_dir = self.root / "config"
        self._app = _load_yaml(self.config_dir / "app.yaml")
        self._geography_raw = _load_yaml(self.config_dir / "geography.yaml")
        self._sources_raw = _load_yaml(self.config_dir / "sources.yaml")
        self._enso_raw = _load_yaml(self.config_dir / "enso.yaml")
        self._drought_raw = _load_yaml(self.config_dir / "drought.yaml")
        self._cyclone_raw = _load_yaml(self.config_dir / "tropical_cyclones.yaml")
        self._alerts_raw = _load_yaml(self.config_dir / "alerts.yaml")
        self._validate()

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #
    def _validate(self) -> None:
        required = ["app", "data", "server"]
        for key in required:
            if key not in self._app:
                raise ConfigError(f"app.yaml missing required section: {key}")
        # Parse entities and sources eagerly to surface schema errors at startup.
        self.geography_entities()
        self.sources()
        self.enso_episodes()
        self.alert_thresholds()

    # ------------------------------------------------------------------ #
    # App settings
    # ------------------------------------------------------------------ #
    @property
    def app(self) -> dict[str, Any]:
        return self._app["app"]

    @property
    def name(self) -> str:
        return self._app["app"].get("name", "COFA FORWARD")

    @property
    def subtitle(self) -> str:
        return self._app["app"].get("subtitle", "")

    @property
    def map_center(self) -> tuple[float, float]:
        c = self._app["app"].get("map_center", {"lat": 6.5, "lon": 152.0})
        return float(c["lat"]), float(c["lon"])

    @property
    def default_units(self) -> str:
        return self._app["app"].get("default_units", "metric")

    @property
    def data_root(self) -> Path:
        root = self._app["data"].get("root", "data")
        p = Path(root)
        return p if p.is_absolute() else self.root / p

    def data_dir(self, key: str) -> Path:
        d = self._app["data"].get("dirs", {}).get(key, key)
        p = Path(d)
        return p if p.is_absolute() else self.root / p

    @property
    def cache_ttl_seconds(self) -> int:
        return int(self._app["data"].get("cache_ttl_seconds", 900))

    @property
    def baseline_min_years(self) -> int:
        return int(self._app.get("scientific", {}).get("baseline_min_years", 15))

    @property
    def llm(self) -> dict[str, Any]:
        return self._app.get("llm", {"enabled": False})

    def ensure_data_dirs(self) -> None:
        for key in ("raw", "interim", "processed", "samples", "cache"):
            self.data_dir(key).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Geography
    # ------------------------------------------------------------------ #
    def geography_entities(self) -> list[GeoEntity]:
        raw = self._geography_raw.get("entities", [])
        return [GeoEntity(**e) for e in raw]

    @property
    def geography_status(self) -> str:
        return self._geography_raw.get("status", "seed")

    # ------------------------------------------------------------------ #
    # Sources
    # ------------------------------------------------------------------ #
    def sources(self) -> list[SourceRecord]:
        raw = self._sources_raw.get("sources", [])
        return [SourceRecord(**s) for s in raw]

    # ------------------------------------------------------------------ #
    # ENSO
    # ------------------------------------------------------------------ #
    @property
    def enso_current(self) -> dict[str, Any]:
        return self._enso_raw.get("current_state", {})

    def enso_episodes(self) -> list[EnsoEpisode]:
        raw = self._enso_raw.get("episodes", [])
        return [EnsoEpisode(**e) for e in raw]

    @property
    def oni_thresholds(self) -> dict[str, Any]:
        return self._enso_raw.get("oni_thresholds", {})

    # ------------------------------------------------------------------ #
    # Drought
    # ------------------------------------------------------------------ #
    @property
    def drought(self) -> dict[str, Any]:
        return self._drought_raw.get("drought", {})

    @property
    def spi(self) -> dict[str, Any]:
        return self._drought_raw.get("spi", {})

    @property
    def freshwater(self) -> dict[str, Any]:
        return self._drought_raw.get("freshwater", {})

    # ------------------------------------------------------------------ #
    # Cyclones
    # ------------------------------------------------------------------ #
    @property
    def cyclone(self) -> dict[str, Any]:
        return self._cyclone_raw.get("tropical_cyclones", {})

    # ------------------------------------------------------------------ #
    # Alerts
    # ------------------------------------------------------------------ #
    def alert_thresholds(self) -> list[AlertThreshold]:
        raw = self._alerts_raw.get("alerts", [])
        return [AlertThreshold(**a) for a in raw]

    # ------------------------------------------------------------------ #
    # Environment / secrets
    # ------------------------------------------------------------------ #
    @staticmethod
    def env(name: str, default: str | None = None) -> str | None:
        """Read an environment variable (secrets never logged)."""
        return os.environ.get(name, default)


@lru_cache(maxsize=1)
def get_config(root: Path | str | None = None) -> Config:
    """Return a cached, validated Config (singleton per process)."""
    return Config(root)
