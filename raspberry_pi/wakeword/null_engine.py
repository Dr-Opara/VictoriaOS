"""Explicit no-op wake-word engine.

Used when no trained model is available. It never claims a detection - the
voice node falls back to VAD-triggered recording and lets the Mini PC's
existing text-based wake-word gate (``backend/voice/wakeword.py``, exercised
after STT) decide whether "Hello Victoria" was actually said. That gate is
real and already tested; this class just makes explicit that *local*,
always-listening wake-word detection is unavailable until a model is
trained, rather than silently doing nothing.
"""

from __future__ import annotations

from raspberry_pi.wakeword.base import WakeWordEngine


class NullWakeWordEngine(WakeWordEngine):
    """A wake-word engine that is never ready and never detects anything."""

    def process(self, pcm_frame: bytes) -> float:
        return 0.0

    def reset(self) -> None:
        return None

    @property
    def is_ready(self) -> bool:
        return False
