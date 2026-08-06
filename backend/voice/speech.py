from __future__ import annotations

import io
import time

from openai import APIError, OpenAI

from backend.config.settings import get_settings
from backend.core.logger import logger

# Extensions/filenames OpenAI's transcription API accepts. Whisper actually
# sniffs content rather than trusting the extension, but the SDK requires a
# filename with a "plausible" suffix on the file-like object.
SUPPORTED_FILENAME_SUFFIXES = (
    ".wav",
    ".mp3",
    ".mp4",
    ".m4a",
    ".mpeg",
    ".mpga",
    ".webm",
    ".ogg",
    ".flac",
)


class TranscriptionError(RuntimeError):
    """Raised when the STT provider fails or is unreachable."""


class SpeechService:
    """Speech-to-text powered by the OpenAI transcription API.

    ``transcribe`` performs a single-shot transcription of a finished audio
    clip. Every call logs latency (never the audio content or API key) so
    slow transcriptions are visible in the logs without exposing secrets.
    """

    def __init__(self, model: str = "whisper-1") -> None:
        self.settings = get_settings()
        self.model = model
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    def transcribe(self, audio: bytes, filename: str = "audio.wav") -> str:
        """Transcribe a complete audio clip and return the recognized text.

        Returns ``""`` for empty input. Raises :class:`TranscriptionError`
        (never the raw OpenAI exception, which could include request
        details) if the provider call fails.
        """
        if not audio:
            logger.info("Transcription skipped: empty audio.")
            return ""

        if not filename.lower().endswith(SUPPORTED_FILENAME_SUFFIXES):
            logger.warning(
                "Transcription requested with an unrecognized filename suffix (%s); "
                "the STT provider may reject it.",
                filename,
            )

        start_time = time.monotonic()
        try:
            audio_file = io.BytesIO(audio)
            audio_file.name = filename
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
            )
        except APIError as error:
            latency_ms = (time.monotonic() - start_time) * 1000
            logger.error(
                "Transcription failed | bytes=%d latency_ms=%.1f error_type=%s",
                len(audio),
                latency_ms,
                type(error).__name__,
            )
            raise TranscriptionError("Speech-to-text provider request failed.") from error
        except Exception as error:
            logger.exception("Unexpected transcription failure.")
            raise TranscriptionError("Speech-to-text failed unexpectedly.") from error

        latency_ms = (time.monotonic() - start_time) * 1000
        text = response.text.strip()
        logger.info(
            "Transcription complete | bytes=%d latency_ms=%.1f chars=%d",
            len(audio),
            latency_ms,
            len(text),
        )
        return text

    def transcribe_chunks(self, chunks: list[bytes]) -> list[str]:
        """Transcribe a sequence of audio chunks, one transcript per chunk."""
        return [self.transcribe(chunk) for chunk in chunks if chunk]
