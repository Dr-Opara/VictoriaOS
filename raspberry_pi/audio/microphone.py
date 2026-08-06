"""Microphone capture: yields raw 16-bit PCM chunks from the selected input device."""

from __future__ import annotations

import queue
from collections.abc import Iterator

from raspberry_pi.audio.devices import AudioDevice, get_sounddevice_backend, select_input_device
from raspberry_pi.logging_config import get_logger

logger = get_logger()


class Microphone:
    """Captures audio from an input device as a stream of PCM chunks.

    Usage::

        with Microphone(sample_rate=16000) as mic:
            for chunk in mic.chunks():
                ...  # bytes of 16-bit little-endian mono PCM
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        frame_ms: int = 30,
        device_hint: str = "",
        sd_module=None,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_samples = int(sample_rate * frame_ms / 1000)
        self._sd = sd_module or get_sounddevice_backend()
        self.device: AudioDevice = select_input_device(device_hint, sd_module=self._sd)
        self._queue: queue.Queue[bytes] = queue.Queue()
        self._stream = None

    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            logger.warning("Microphone input status: %s", status)
        self._queue.put(bytes(indata))

    def __enter__(self) -> Microphone:
        self.start()
        return self

    def __exit__(self, *_exc_info) -> None:
        self.stop()

    def start(self) -> None:
        """Open the input stream and begin buffering audio."""
        self._stream = self._sd.RawInputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.device.index,
            dtype="int16",
            blocksize=self.frame_samples,
            callback=self._callback,
        )
        self._stream.start()
        logger.info("Microphone started on %s @ %sHz", self.device.name, self.sample_rate)

    def stop(self) -> None:
        """Stop and close the input stream."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            logger.info("Microphone stopped.")

    def chunks(self) -> Iterator[bytes]:
        """Yield raw PCM chunks as they arrive, until the stream is stopped."""
        while self._stream is not None:
            try:
                yield self._queue.get(timeout=1.0)
            except queue.Empty:
                continue
