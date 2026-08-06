from __future__ import annotations

from openai import OpenAI

from backend.config.settings import get_settings
from backend.core.logger import logger


class EmbeddingService:
    """Generates text embeddings via the OpenAI embeddings API."""

    def __init__(self, model: str | None = None) -> None:
        self.settings = get_settings()
        self.model = model or self.settings.embedding_model
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text, in the same order."""
        if not texts:
            return []

        try:
            response = self.client.embeddings.create(model=self.model, input=texts)
        except Exception:
            logger.exception("Embedding generation failed.")
            raise

        return [item.embedding for item in response.data]

    def embed_one(self, text: str) -> list[float]:
        """Return the embedding vector for a single text."""
        return self.embed([text])[0]
