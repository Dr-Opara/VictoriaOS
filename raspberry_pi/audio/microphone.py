"""Microphone capture: yields raw 16-bit PCM chunks from the selected input device."""

from __future__ import annotations

import queue
from collections.abc import Iterator
from typing import Any

from raspberry_pi.audio.devices import AudioDevice, get_sounddevice_backend, select_input_device
from raspberry_pi.logging_config import get_logger

logger = get_logger()


class MicrophoneDisconnectedError(RuntimeError):
    """Raised when the input device stops streaming (unplugged, driver error, etc.)."""


class Microphone:
    """Captures audio from an input device as a stream of PCM chunks.

    Usage::

        with Microphone(sample_rate=16000) as mic:
            for chunk in mic.chunks():
                ...  # bytes of 16-bit little-endian mono PCM

    If the device is unplugged (or otherwise stops streaming) mid-capture,
    :meth:`chunks` raises :class:`MicrophoneDisconnectedError` instead of
    hanging forever waiting for audio that will never arrive - callers
    (``VoiceNode``) are expected to catch this, log it clearly, and retry
    device selection rather than silently continuing with no input.
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
        self._stream: Any | None = None
        self._stream_error: Exception | None = None
        self._stopping = False

    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            # PortAudio reports overflow/underflow and similar conditions here;
            # log them but keep streaming - they aren't necessarily fatal.
            logger.warning("Microphone input status: %s", status)
        self._queue.put(bytes(indata))

    def _abort_callback(self, exception: Exception) -> None:
        """Called by PortAudio when the stream aborts (e.g. device removed)."""
        self._stream_error = exception
        logger.error("Microphone stream aborted: %s", exception)

    def __enter__(self) -> Microphone:
        self.start()
        return self

    def __exit__(self, *_exc_info) -> None:
        self.stop()

    def start(self) -> None:
        """Open the input stream and begin buffering audio."""
        try:
            self._stream = self._sd.RawInputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device.index,
                dtype="int16",
                blocksize=self.frame_samples,
                callback=self._callback,
                finished_callback=self._on_stream_finished,
            )
            self._stream.start()
        except Exception as error:
            raise MicrophoneDisconnectedError(
                f"Could not open microphone {self.device.name!r}: {error}"
            ) from error

        self._stream_error = None
        self._stopping = False
        logger.info("Microphone started on %s @ %sHz", self.device.name, self.sample_rate)

    def _on_stream_finished(self) -> None:
        if not self._stopping:
            logger.warning("Microphone stream finished unexpectedly (device removed?).")

    def stop(self) -> None:
        """Stop and close the input stream."""
        if self._stream is not None:
            self._stopping = True
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:  # pragma: no cover - defensive, PortAudio may already be dead
                logger.exception("Error while stopping microphone stream.")
            finally:
                self._stream = None
                logger.info("Microphone stopped.")

    def chunks(self) -> Iterator[bytes]:
        """Yield raw PCM chunks as they arrive, until the stream is stopped.

        Raises :class:`MicrophoneDisconnectedError` if the underlying stream
        reports an error or is no longer active (rather than hanging).
        """
        while self._stream is not None:
            if self._stream_error is not None:
                raise MicrophoneDisconnectedError(
                    f"Microphone {self.device.name!r} reported an error: {self._stream_error}"
                )
            if not self._stream.active:
                raise MicrophoneDisconnectedError(
                    f"Microphone {self.device.name!r} is no longer active - "
                    "it may have been unplugged."
                )

            try:
                yield self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

    def drain(self) -> int:
        """Discard any buffered chunks (e.g. captured while Victoria was
        speaking) so the next turn doesn't start with stale audio. Returns
        the number of chunks discarded.
        """
        discarded = 0
        while True:
            try:
                self._queue.get_nowait()
                discarded += 1
            except queue.Empty:
                break
        return discarded
