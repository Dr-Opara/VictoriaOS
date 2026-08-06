"""Selects a wake-word engine implementation based on configuration."""

from __future__ import annotations

from raspberry_pi.config import PiConfig
from raspberry_pi.wakeword.base import WakeWordEngine
from raspberry_pi.wakeword.null_engine import NullWakeWordEngine
from raspberry_pi.wakeword.openwakeword_engine import OpenWakeWordEngine


def create_wakeword_engine(config: PiConfig) -> WakeWordEngine:
    """Build the configured wake-word engine, falling back to a no-op.

    Never raises - a missing model or missing dependency degrades to
    :class:`NullWakeWordEngine` rather than crashing the voice node.
    """
    if not config.wake_word_model_path:
        return NullWakeWordEngine()

    engine = OpenWakeWordEngine(config.wake_word_model_path, threshold=config.wake_word_threshold)
    if engine.is_ready:
        return engine

    return NullWakeWordEngine()
