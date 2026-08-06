"""Speaker playback: plays WAV audio (as returned by the Mini PC's TTS) on the
selected output device, with support for interrupting playback mid-clip.
"""

from __future__ import annotations

import io
import threading
import wave

from raspberry_pi.audio.devices import AudioDevice, get_sounddevice_backend, select_output_device
from raspberry_pi.logging_config import get_logger

logger = get_logger()


class SpeakerDisconnectedError(RuntimeError):
    """Raised when the output device can't be opened or fails during playback."""


class Speaker:
    """Plays WAV audio bytes on an output device, stoppable mid-playback.

    Playback is single-flight: starting a new clip while one is already
    playing stops the previous one first, so two replies can never overlap
    on the speaker.
    """

    def __init__(self, device_hint: str = "", sd_module=None) -> None:
        self._sd = sd_module or get_sounddevice_backend()
        self.device: AudioDevice = select_output_device(device_hint, sd_module=self._sd)
        self._stop_event = threading.Event()
        self._playback_done = threading.Event()
        self._playback_done.set()
        self._lock = threading.Lock()
        self.last_error: Exception | None = None

    @property
    def is_playing(self) -> bool:
        """Whether a clip is currently being played back."""
        return not self._playback_done.is_set()

    def play(self, wav_bytes: bytes, block: bool = True) -> None:
        """Play a WAV clip, interrupting any clip already playing.

        If ``block`` is False, returns immediately and playback can be
        polled via :attr:`is_playing` or cancelled with :meth:`stop`.
        """
        with self._lock:
            if self.is_playing:
                self.stop()
                self._playback_done.wait(timeout=2.0)

            try:
                with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    frames = wav_file.readframes(wav_file.getnframes())
            except wave.Error as error:
                raise ValueError(f"Unsupported or corrupt WAV audio: {error}") from error

            dtype = {1: "int8", 2: "int16", 4: "int32"}.get(sample_width, "int16")

            self._stop_event.clear()
            self._playback_done.clear()
            self.last_error = None

            if block:
                self._run_playback(frames, dtype, sample_rate, channels)
            else:
                threading.Thread(
                    target=self._run_playback,
                    args=(frames, dtype, sample_rate, channels),
                    daemon=True,
                ).start()

    def _run_playback(self, frames: bytes, dtype: str, sample_rate: int, channels: int) -> None:
        import numpy as np

        try:
            audio = np.frombuffer(frames, dtype=dtype).reshape(-1, channels)
            stream = self._sd.OutputStream(
                samplerate=sample_rate,
                channels=channels,
                device=self.device.index,
                dtype=dtype,
            )
            try:
                stream.start()
            except Exception as error:
                raise SpeakerDisconnectedError(
                    f"Could not open speaker {self.device.name!r}: {error}"
                ) from error

            try:
                chunk_size = sample_rate // 10 or 1
                for start in range(0, len(audio), chunk_size):
                    if self._stop_event.is_set():
                        logger.info("Playback interrupted.")
                        break
                    stream.write(audio[start : start + chunk_size])
            finally:
                stream.stop()
                stream.close()
        except SpeakerDisconnectedError as error:
            logger.error("Speaker disconnected during playback.")
            self.last_error = error
            raise
        finally:
            self._playback_done.set()

    def stop(self) -> None:
        """Stop any in-progress playback (used for barge-in/interruption)."""
        self._stop_event.set()
