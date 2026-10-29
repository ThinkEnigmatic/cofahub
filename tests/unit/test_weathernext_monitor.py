"""WeatherNext approval monitor tests (offline, pure classify logic)."""

from __future__ import annotations

import sys
from pathlib import Path

# Import the monitor script directly (it's in scripts/, not a package).
_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from monitor_weathernext_approval import classify  # noqa: E402


def _row(subject: str, text: str) -> dict:
    return {"subject": subject, "text": text, "from": "weathernext@google.com", "date": "x"}


def test_classify_pending_when_no_messages():
    assert classify([]) == "pending"


def test_classify_pending_when_candidate_without_decision():
    rows = [_row("WeatherNext access request received", "Thank you for your request.")]
    assert classify(rows) == "pending"


def test_classify_approved():
    rows = [_row("WeatherNext access", "Your access has been approved. You now have access.")]
    assert classify(rows) == "approved"


def test_classify_rejected():
    rows = [_row("WeatherNext", "We are unable to grant access at this time.")]
    assert classify(rows) == "rejected"


def test_classify_newest_wins():
    rows = [
        _row("WeatherNext", "approved — you now have access"),
        _row("WeatherNext", "denied"),
    ]
    # rows are newest-first; first decision-bearing message is approved
    assert classify(rows) == "approved"
