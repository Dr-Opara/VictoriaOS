"""Logging setup for the Raspberry Pi voice node.

Mirrors ``backend/core/logger.py``'s shape (console + rotating file) but is
kept independent since this package must not depend on ``backend``.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from raspberry_pi.config import get_config

_LOGGER_NAME = "VictoriaVoiceNode"


def get_logger() -> logging.Logger:
    """Return the shared voice-node logger, configuring it on first call."""
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger

    config = get_config()
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    file_handler = RotatingFileHandler(
        log_dir / "voice_node.log", maxBytes=5_000_000, backupCount=3
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


logger = get_logger()
