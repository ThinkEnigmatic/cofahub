"""Logging configuration.

Centralized, secrets-aware logging. Credentials must never be written to logs.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def setup_logging(level: str = "INFO", file: str | Path | None = None) -> logging.Logger:
    """Configure root logging and return the package logger.

    Parameters
    ----------
    level:
        Log level name (e.g. "INFO", "DEBUG").
    file:
        Optional path for a rotating-free plain file handler (parent dirs are
        created). Streams to stderr regardless.

    Returns
    -------
    The ``cofa_forward`` logger.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers on repeated calls (e.g. Streamlit reruns).
    if not any(getattr(h, "_cofa", False) for h in root.handlers):
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(logging.Formatter(_FORMAT))
        sh._cofa = True  # type: ignore[attr-defined]
        root.addHandler(sh)

        if file is not None:
            path = Path(file)
            path.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(path, encoding="utf-8")
            fh.setFormatter(logging.Formatter(_FORMAT))
            fh._cofa = True  # type: ignore[attr-defined]
            root.addHandler(fh)

    return logging.getLogger("cofa_forward")
