from __future__ import annotations

import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

_audit_logger = logging.getLogger("VictoriaOS.audit")
_audit_logger.setLevel(logging.INFO)
_audit_logger.propagate = False

if not _audit_logger.handlers:
    handler = logging.FileHandler(LOG_DIR / "audit.log")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    _audit_logger.addHandler(handler)


def audit_log(action: str, detail: str) -> None:
    """Record a sensitive action (memory/task mutation, etc.) to the audit log."""
    _audit_logger.info("%s | %s", action, detail)
