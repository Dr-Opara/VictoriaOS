from __future__ import annotations

from collections.abc import Iterator

from openai import OpenAI

from backend.config.settings import get_settings
from backend.core.logger import logger


class TextToSpeech:
    """Text-to-speech powered by the OpenAI audio API.

    ``speak`` is kept for backward compatibility (console echo, used by
    tests and CLI-style flows). ``synthesize``/``stream`` produce real audio
    bytes for the voice pipeline.
    """

    def __init__(self, model: str = "gpt-4o-mini-tts", voice: str = "alloy") -> None:
        self.settings = get_settings()
        self.model = model
        self.voice = voice
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    def speak(self, text: str) -> None:
        """Print what Victoria would say (used by lightweight/text flows)."""
        print(f"Victoria: {text}")

    def synthesize(self, text: str) -> bytes:
        """Return synthesized speech audio (MP3 bytes) for ``text``."""
        try:
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
            )
            return response.read()
        except Exception:
            logger.exception("Text-to-speech synthesis failed.")
            raise

    def stream(self, text: str) -> Iterator[bytes]:
        """Yield synthesized speech audio incrementally as it is generated."""
        try:
            with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=text,
            ) as response:
                yield from response.iter_bytes()
        except Exception:
            logger.exception("Streaming text-to-speech synthesis failed.")
            raise
