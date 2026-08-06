from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    chunk_id: int
    document_id: int
    text: str
    score: float


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Return the cosine similarity between two vectors."""
    vector_a = np.asarray(a, dtype=np.float64)
    vector_b = np.asarray(b, dtype=np.float64)

    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(vector_a, vector_b) / (norm_a * norm_b))


def rank_chunks(
    query_embedding: list[float],
    candidates: list[tuple[int, int, str, list[float]]],
    limit: int = 5,
) -> list[ScoredChunk]:
    """Rank ``candidates`` (chunk_id, document_id, text, embedding) by similarity.

    A brute-force in-memory ranking - appropriate for a personal knowledge
    base at this scale (hundreds to low thousands of chunks). A dedicated
    vector index (e.g. FAISS/pgvector) would be the natural next step if
    the corpus grows well beyond that; tracked in the roadmap, not a
    blocker for a working semantic search today.
    """
    scored = [
        ScoredChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            text=text,
            score=cosine_similarity(query_embedding, embedding),
        )
        for chunk_id, document_id, text, embedding in candidates
    ]
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]
