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


class Speaker:
    """Plays WAV audio bytes on an output device, stoppable mid-playback."""

    def __init__(self, device_hint: str = "", sd_module=None) -> None:
        self._sd = sd_module or get_sounddevice_backend()
        self.device: AudioDevice = select_output_device(device_hint, sd_module=self._sd)
        self._stop_event = threading.Event()

    def play(self, wav_bytes: bytes, block: bool = True) -> None:
        """Play a WAV clip. If ``block`` is False, returns immediately and
        playback can be cancelled with :meth:`stop`.
        """
        self._stop_event.clear()

        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            frames = wav_file.readframes(wav_file.getnframes())

        dtype = {1: "int8", 2: "int16", 4: "int32"}.get(sample_width, "int16")

        def _play() -> None:
            import numpy as np

            audio = np.frombuffer(frames, dtype=dtype).reshape(-1, channels)
            stream = self._sd.OutputStream(
                samplerate=sample_rate,
                channels=channels,
                device=self.device.index,
                dtype=dtype,
            )
            stream.start()
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

        if block:
            _play()
        else:
            threading.Thread(target=_play, daemon=True).start()

    def stop(self) -> None:
        """Stop any in-progress playback (used for barge-in/interruption)."""
        self._stop_event.set()
