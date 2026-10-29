"""Monitor the household Gmail inbox for the WeatherNext access decision.

Polls ``hemingwayglobal77@gmail.com`` over IMAP (app password, no OAuth) for any
message from/to Google about WeatherNext, classifies it as ``pending`` /
``approved`` / ``rejected``, writes a status file the app can read, and notifies
the owner over Telegram on the first state change (or on ``--notify``).

Usage:
    uv run python scripts/monitor_weathernext_approval.py [--notify] [--check]

State file: ``data/weathernext_status.json`` (committed location, git-ignored).

The app's Data Sources page reads the same file to show the live approval state.
"""

from __future__ import annotations

import argparse
import email
import imaplib
import json
import re
import sys
from datetime import UTC, datetime
from email.header import decode_header
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

HOST = "imap.gmail.com"
USER = "hemingwayglobal77@gmail.com"
PASSWORD_FILE = Path.home() / ".config" / "benigmatic" / "gmail_household_app_password"

# Paths (resolve against the repo root, not CWD).
_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = _ROOT / "data" / "weathernext_status.json"
LOG_FILE = Path.home() / "Library" / "Logs" / "cofaforward-weathernext-monitor.log"

# Keywords that indicate the WeatherNext decision. Broad match: any message whose
# From or Subject mentions weathernext is a candidate; body is scanned for the
# approval/rejection verbs.
_CANDIDATE = re.compile(r"weathernext|weather next|deepmind.*weather", re.I)
_APPROVED = re.compile(
    r"\b(approved|access granted|granted access|you now have access|"
    r"has been approved|welcome to weathernext)\b",
    re.I,
)
_REJECTED = re.compile(
    r"\b(denied|not approved|cannot (grant|prioritize)|unable to (grant|approve)|"
    r"request.*(declined|rejected))\b",
    re.I,
)


def _log(msg: str) -> None:
    line = f"{datetime.now(UTC).isoformat()} {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def _decode(value: str | None) -> str:
    if not value:
        return ""
    out = []
    for chunk, charset in decode_header(value):
        if isinstance(chunk, bytes):
            out.append(chunk.decode(charset or "utf-8", "replace"))
        else:
            out.append(chunk)
    return "".join(out)


def _body_text(message) -> str:
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(
                part.get("Content-Disposition") or ""
            ):
                payload = part.get_payload(decode=True) or b""
                return payload.decode(part.get_content_charset() or "utf-8", "replace")
        return ""
    payload = message.get_payload(decode=True) or b""
    return payload.decode(message.get_content_charset() or "utf-8", "replace")


def _password() -> str | None:
    if not PASSWORD_FILE.is_file():
        return None
    return PASSWORD_FILE.read_text().strip() or None


def fetch_weathernext_messages(limit: int = 30, timeout: float = 30) -> dict:
    """Return any WeatherNext-related messages in the inbox."""
    secret = _password()
    if not secret:
        return {"ok": False, "error": f"no app password at {PASSWORD_FILE}"}
    try:
        client = imaplib.IMAP4_SSL(HOST, 993, timeout=timeout)
        client.login(USER, secret)
        client.select("INBOX")
        status, data = client.search(None, "ALL")
        if status != "OK":
            return {"ok": False, "error": f"search failed: {status}"}
        ids = data[0].split()[-max(1, int(limit)) :]
        rows = []
        for uid in reversed(ids):
            status, payload = client.fetch(uid, "(RFC822)")
            if status != "OK" or not payload or not isinstance(payload[0], tuple):
                continue
            message = email.message_from_bytes(payload[0][1])
            sender = _decode(message.get("From"))
            subject = _decode(message.get("Subject"))
            body = _body_text(message)
            if not _CANDIDATE.search(f"{sender} {subject} {body[:2000]}"):
                continue
            rows.append(
                {
                    "id": uid.decode(),
                    "from": sender,
                    "subject": subject,
                    "date": _decode(message.get("Date")),
                    "text": body[:4000],
                }
            )
        client.logout()
        return {"ok": True, "account": USER, "rows": rows}
    except Exception as exc:  # noqa: BLE001 - surface network/IMAP errors
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def classify(rows: list[dict]) -> str:
    """pending | approved | rejected — based on the latest decision-bearing body."""
    if not rows:
        return "pending"
    for row in rows:  # newest first
        text = f"{row['subject']}\n{row['text']}"
        if _APPROVED.search(text):
            return "approved"
        if _REJECTED.search(text):
            return "rejected"
    return "pending"


def load_state() -> dict:
    if STATE_FILE.is_file():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def notify(text: str) -> bool:
    """Notify the owner over Telegram (ai-dev telegram send)."""
    import subprocess

    ai_dev = "/Users/ben/ai-orchestrator/bin/ai-dev"
    try:
        subprocess.run([ai_dev, "telegram", "send", text], check=True, timeout=60)
        return True
    except (subprocess.SubprocessError, OSError) as exc:
        _log(f"telegram notify failed: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--notify", action="store_true", help="Notify Telegram on change.")
    parser.add_argument("--check", action="store_true", help="Re-check even if unchanged.")
    args = parser.parse_args()

    result = fetch_weathernext_messages()
    if not result.get("ok"):
        _log(f"IMAP error: {result.get('error')}")
        return 1

    rows = result["rows"]
    state = load_state()
    previous = state.get("status", "pending")
    status = classify(rows)
    checked_at = datetime.now(UTC).isoformat()

    # Find the latest decision-bearing message (for the record).
    latest = rows[0] if rows else None

    new_state = {
        "status": status,
        "checked_at": checked_at,
        "account": USER,
        "n_candidate_messages": len(rows),
        "latest_message": (
            {
                "from": latest["from"],
                "subject": latest["subject"],
                "date": latest["date"],
            }
            if latest
            else None
        ),
        "form_submitted": "2026-10-29",
        "form_contact": "weathernext@google.com",
        "approval_window": "typically 5-7 business days",
    }
    save_state(new_state)

    changed = status != previous or args.check
    _log(f"status={status} candidates={len(rows)} (prev={previous})")

    if latest:
        print(f"Latest WeatherNext message: {latest['from']} | {latest['subject']}")
    print(f"WeatherNext access status: {status.upper()}")

    if changed and args.notify:
        if status == "approved":
            msg = (
                "✅ WeatherNext access APPROVED for hemingwayglobal77@gmail.com. "
                "Next: set GOOGLE_APPLICATION_CREDENTIALS (or gcloud auth "
                "application-default login)."
            )
        elif status == "rejected":
            msg = (
                "⚠️ WeatherNext request was NOT approved (or couldn't be "
                "prioritized). See the inbox."
            )
        else:
            msg = f"ℹ️ WeatherNext: {len(rows)} candidate message(s) seen, decision still pending."
        notify(msg)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
