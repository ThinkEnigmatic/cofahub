"""Generate the daily Markdown intelligence brief.

Usage:  uv run python scripts/generate_report.py [--out FILE]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cofa_forward.ui.pages.reports import assemble_brief  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the daily brief.")
    parser.add_argument("--out", type=str, default=None, help="Write to file instead of stdout.")
    args = parser.parse_args()

    brief = assemble_brief()
    if args.out:
        Path(args.out).write_text(brief, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(brief)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
