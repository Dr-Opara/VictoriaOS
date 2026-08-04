from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class SpeechSegment:
    """A span of detected speech within a PCM stream, in seconds."""

    start_seconds: float
    end_seconds: float


class VoiceActivityDetector:
    """Energy-based voice activity detection for 16-bit mono PCM audio.

    This is a lightweight, dependency-free VAD (numpy only) suitable for
    trimming silence before STT and for detecting silence/interruption
    during conversation mode. It is not as accurate as a trained VAD model
    (e.g. WebRTC VAD or Silero), but requires no extra native dependencies
    and works well enough to gate STT calls and drive turn-taking.
    """

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

    def _frames(self, pcm: bytes) -> np.ndarray:
        samples = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
        frame_samples = self._frame_samples()
        usable_length = (len(samples) // frame_samples) * frame_samples
        if usable_length == 0:
            return np.empty((0, frame_samples), dtype=np.float32)

        return samples[:usable_length].reshape(-1, frame_samples)

    def frame_energies(self, pcm: bytes) -> np.ndarray:
        """Return the RMS energy of each frame in the given PCM audio."""
        frames = self._frames(pcm)
        if frames.size == 0:
            return np.empty(0, dtype=np.float32)

        return np.sqrt(np.mean(np.square(frames), axis=1))

    def is_speech(self, pcm: bytes) -> bool:
        """Return ``True`` if the given PCM chunk contains speech energy."""
        energies = self.frame_energies(pcm)
        if energies.size == 0:
            return False

        return bool(np.max(energies) >= self.energy_threshold)

    def trailing_silence_ms(self, pcm: bytes) -> float:
        """Return how many trailing milliseconds of ``pcm`` are silence."""
        energies = self.frame_energies(pcm)
        if energies.size == 0:
            return 0.0

        silent_frames = 0
        for energy in energies[::-1]:
            if energy >= self.energy_threshold:
                break
            silent_frames += 1

        return silent_frames * self.frame_ms

    def has_endpointed(self, pcm: bytes) -> bool:
        """Return ``True`` once trailing silence exceeds ``silence_hold_ms``.

        Used to detect that the user has finished speaking (end of turn).
        """
        return self.trailing_silence_ms(pcm) >= self.silence_hold_ms

    def speech_segments(self, pcm: bytes) -> list[SpeechSegment]:
        """Return contiguous speech segments detected in ``pcm``, in seconds."""
        energies = self.frame_energies(pcm)
        segments: list[SpeechSegment] = []
        frame_seconds = self.frame_ms / 1000

        in_speech = False
        start_frame = 0
        for index, energy in enumerate(energies):
            speaking = energy >= self.energy_threshold
            if speaking and not in_speech:
                in_speech = True
                start_frame = index
            elif not speaking and in_speech:
                in_speech = False
                segments.append(
                    SpeechSegment(start_frame * frame_seconds, index * frame_seconds)
                )

        if in_speech:
            segments.append(
                SpeechSegment(start_frame * frame_seconds, len(energies) * frame_seconds)
            )

        return segments
