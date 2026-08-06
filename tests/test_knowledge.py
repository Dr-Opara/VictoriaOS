from backend.knowledge.documents import UnsupportedDocumentError, chunk_text, extract_text
from backend.knowledge.manager import KnowledgeManager
from backend.knowledge.search import cosine_similarity, rank_chunks


class FakeEmbeddingService:
    """Deterministic fake: embeds text as a one-hot vector over keywords."""

    KEYWORDS = ["raspberry", "mini", "wifi", "password", "unrelated"]

    def embed(self, texts):
        return [self.embed_one(text) for text in texts]

    def embed_one(self, text):
        lowered = text.lower()
        return [1.0 if keyword in lowered else 0.0 for keyword in self.KEYWORDS]


class FakeAIGateway:
    def ask(self, prompt, instructions=None):
        return f"ANSWER::{prompt}"


def _manager() -> KnowledgeManager:
    return KnowledgeManager(embeddings=FakeEmbeddingService(), ai=FakeAIGateway())


def test_extract_text_plain():
    assert extract_text("notes.txt", b"hello world") == "hello world"


def test_extract_text_unsupported_extension_raises():
    try:
        extract_text("archive.zip", b"data")
        assert False, "expected UnsupportedDocumentError"
    except UnsupportedDocumentError:
        pass


def test_chunk_text_splits_with_overlap():
    text = "word " * 500
    chunks = chunk_text(text, chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_chunk_text_empty_returns_no_chunks():
    assert chunk_text("   ") == []


def test_cosine_similarity_identical_vectors_is_one():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_cosine_similarity_orthogonal_vectors_is_zero():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_rank_chunks_orders_by_similarity():
    candidates = [
        (1, 1, "a", [1.0, 0.0]),
        (2, 1, "b", [0.0, 1.0]),
    ]
    ranked = rank_chunks([1.0, 0.0], candidates, limit=2)
    assert ranked[0].chunk_id == 1
    assert ranked[0].score > ranked[1].score


def test_ingest_and_search_document():
    manager = _manager()
    summary = manager.ingest("wifi.txt", b"The wifi password is set on the Raspberry Pi.")

    assert summary.filename == "wifi.txt"
    assert summary.chunk_count == 1

    results = manager.search("raspberry", limit=3)
    assert len(results) == 1
    assert "wifi" in results[0].text.lower()


def test_list_and_delete_document():
    manager = _manager()
    summary = manager.ingest("notes.txt", b"unrelated content here")

    documents = manager.list_documents()
    assert any(doc.id == summary.id for doc in documents)

    assert manager.delete_document(summary.id) is True
    assert manager.delete_document(summary.id) is False
    assert not any(doc.id == summary.id for doc in manager.list_documents())


def test_ask_with_no_documents_returns_graceful_message():
    manager = _manager()
    result = manager.ask("anything")
    assert "don't have any documents" in result.answer.lower()
    assert result.sources == []


def test_ask_returns_answer_with_sources():
    manager = _manager()
    manager.ingest("wifi.txt", b"The wifi password is hidden on the mini pc.")

    result = manager.ask("mini")
    assert result.answer.startswith("ANSWER::")
    assert result.sources == ["wifi.txt"]
