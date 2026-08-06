"""Pluggable wake-word engine interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class WakeWordEngine(ABC):
    """A streaming wake-word detector.

    Implementations are fed successive audio frames via :meth:`process`,
    which returns a detection confidence in ``[0, 1]`` for that frame (most
    streaming wake-word models score continuously rather than per-utterance).
    """

    @abstractmethod
    def process(self, pcm_frame: bytes) -> float:
        """Score one PCM frame; higher means more likely the wake word."""

    @abstractmethod
    def reset(self) -> None:
        """Clear any internal state (e.g. after a detection fires)."""

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """Whether this engine can actually detect anything right now."""
