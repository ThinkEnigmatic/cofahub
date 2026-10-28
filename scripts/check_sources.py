"""Check data-source status and adapter availability.

Usage:  uv run python scripts/check_sources.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.config import get_config  # noqa: E402
from cofa_forward.ingestion.chirps import ChirpsAdapter  # noqa: E402
from cofa_forward.ingestion.enso import CpcOniAdapter  # noqa: E402
from cofa_forward.ingestion.historical_impacts import HistoricalImpactsAdapter  # noqa: E402
from cofa_forward.ingestion.ibtracs import IbtracsAdapter  # noqa: E402
from cofa_forward.ingestion.jma import JmaTyphoonAdapter  # noqa: E402
from cofa_forward.ingestion.official_advisories import OfficialAdvisoriesAdapter  # noqa: E402
from cofa_forward.ingestion.population import PopulationAdapter  # noqa: E402
from cofa_forward.ingestion.rainfall import OpenMeteoArchiveAdapter  # noqa: E402
from cofa_forward.ingestion.weather import OpenMeteoForecastAdapter  # noqa: E402


def main() -> int:
    cfg = get_config()
    adapters = [
        OpenMeteoForecastAdapter(config=cfg),
        OpenMeteoArchiveAdapter(config=cfg),
        CpcOniAdapter(),
        IbtracsAdapter(),
        JmaTyphoonAdapter(),
        ChirpsAdapter(),
        OfficialAdvisoriesAdapter(),
        PopulationAdapter(),
        HistoricalImpactsAdapter(),
    ]
    print(f"{'source':<24} {'available':<10} note")
    print("-" * 80)
    for a in adapters:
        info = a.check_availability()
        print(f"{a.source_id:<24} {str(info.get('available')):<10} {info.get('note', '')}")
    print()
    print("Configured sources:")
    for s in cfg.sources():
        print(f"  [{s.implementation_status:<22}] {s.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
