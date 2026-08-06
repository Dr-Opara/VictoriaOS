"""Energy-based voice activity detection for the Pi voice node.

This intentionally re-implements the same lightweight technique as
``backend/voice/vad.py`` rather than importing it: the Pi voice node runs in
its own virtual environment with a minimal, hardware-facing dependency set
(numpy + sounddevice + websockets + requests) and must not pull in the full
backend package (FastAPI, SQLAlchemy, the OpenAI server SDK, etc.) just to
reuse a ~40-line algorithm. If the two ever need to diverge (e.g. a real
trained VAD model on the Pi), this boundary makes that safe.
"""

from __future__ import annotations

import numpy as np


class VoiceActivityDetector:
    """Frame-energy VAD over 16-bit mono PCM audio."""

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_ms: int = 30,
        energy_threshold: float = 500.0,
        silence_hold_ms: int = 800,
    ) -> None:
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.energy_threshold = energy_threshold
        self.silence_hold_ms = silence_hold_ms

    def _frame_samples(self) -> int:
        return int(self.sample_rate * self.frame_ms / 1000)

    def frame_energy(self, pcm_chunk: bytes) -> float:
        """Return the RMS energy of a single PCM chunk."""
        samples = np.frombuffer(pcm_chunk, dtype=np.int16).astype(np.float32)
        if samples.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(samples))))

    def is_speech(self, pcm_chunk: bytes) -> bool:
        """Return ``True`` if this chunk's energy is above the speech threshold."""
        return self.frame_energy(pcm_chunk) >= self.energy_threshold


class EndpointDetector:
    """Tracks consecutive silence across streamed chunks to detect end-of-turn.

    Feed it chunks as they arrive from the microphone; once
    ``silence_hold_ms`` worth of consecutive low-energy chunks have been
    seen (after at least one speech chunk), :meth:`push` returns ``True``
    to signal the utterance is complete.
    """

    def __init__(self, vad: VoiceActivityDetector | None = None) -> None:
        self.vad = vad or VoiceActivityDetector()
        self._silence_ms = 0.0
        self._heard_speech = False

    def reset(self) -> None:
        self._silence_ms = 0.0
        self._heard_speech = False

    def push(self, pcm_chunk: bytes) -> bool:
        """Feed one chunk; returns ``True`` once end-of-turn is detected."""
        if self.vad.is_speech(pcm_chunk):
            self._heard_speech = True
            self._silence_ms = 0.0
            return False

        if not self._heard_speech:
            return False

        self._silence_ms += self.vad.frame_ms
        return self._silence_ms >= self.vad.silence_hold_ms
