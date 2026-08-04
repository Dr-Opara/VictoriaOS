from __future__ import annotations

import io

from openai import OpenAI

from backend.config.settings import get_settings
from backend.core.logger import logger


class SpeechService:
    """Speech-to-text powered by the OpenAI transcription API.

    ``transcribe`` performs a single-shot transcription of a finished audio
    clip. ``transcribe_chunks`` supports a streaming-style workflow: the
    caller feeds successive audio chunks (e.g. as VAD detects end-pointed
    speech segments) and receives an incremental transcript for each one,
    which is how continuous listening for the wake word is implemented.
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
        """Transcribe a complete audio clip and return the recognized text."""
        if not audio:
            return ""

        try:
            audio_file = io.BytesIO(audio)
            audio_file.name = filename
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
            )
            return response.text.strip()
        except Exception:
            logger.exception("Speech-to-text transcription failed.")
            raise

    def transcribe_chunks(self, chunks: list[bytes]) -> list[str]:
        """Transcribe a sequence of audio chunks, one transcript per chunk."""
        return [self.transcribe(chunk) for chunk in chunks if chunk]
