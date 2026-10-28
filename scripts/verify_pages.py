"""Verify each Streamlit page renders without exceptions using AppTest.

Run:  uv run python scripts/verify_pages.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(_ROOT / "src" / "cofa_forward" / "ui" / "app.py")

PAGES = [
    "Overview",
    "Weather Operations",
    "ENSO & Climate",
    "Drought & Water",
    "Tropical Cyclones",
    "Historical Impacts",
    "Island Profiles",
    "Reports",
    "Data Sources & System Health",
]


def main() -> int:
    failures = 0
    for page in PAGES:
        at = AppTest.from_file(APP, default_timeout=60)
        at.run()
        # Navigation radio (second radio in sidebar) selects the page.
        radios = at.sidebar.radio
        nav = radios[-1]
        nav.set_value(page)
        at.run()
        if at.exception:
            failures += 1
            print(f"FAIL {page}: {at.exception[0].value}")
        else:
            print(f"OK   {page}")
    print(f"\n{failures} page(s) with exceptions out of {len(PAGES)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
