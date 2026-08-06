from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import delete, select

from backend.core.ai import AIGateway
from backend.core.logger import logger
from backend.database.database import session_scope
from backend.database.models import Document, DocumentChunk
from backend.knowledge.documents import chunk_text, extract_text
from backend.knowledge.embeddings import EmbeddingService
from backend.knowledge.search import ScoredChunk, rank_chunks

_RAG_INSTRUCTIONS = """
You are Victoria, Dr. Opara's private executive AI assistant, answering a
question using excerpts retrieved from his documents.

Rules:
- Answer using only the provided excerpts. If they don't contain the
  answer, say so plainly rather than guessing.
- Cite which document each fact came from by filename.
- Be concise and professional.
""".strip()


@dataclass(frozen=True, slots=True)
class DocumentSummary:
    id: int
    filename: str
    content_type: str
    char_count: int
    chunk_count: int


@dataclass(frozen=True, slots=True)
class RagAnswer:
    answer: str
    sources: list[str]


class KnowledgeManager:
    """Document ingestion, semantic search, and retrieval-augmented answers.

    This is VictoriaOS's long-term document memory: separate from
    ``MemoryService`` (short facts/preferences) but reachable through the
    same conversational surface (see ``VictoriaAssistant`` knowledge-intent
    routing).
    """

    def __init__(
        self, embeddings: EmbeddingService | None = None, ai: AIGateway | None = None
    ) -> None:
        self.embeddings = embeddings or EmbeddingService()
        self.ai = ai or AIGateway()

    def ingest(self, filename: str, content: bytes, content_type: str = "") -> DocumentSummary:
        """Extract, chunk, embed, and store a document."""
        text = extract_text(filename, content)
        chunks = chunk_text(text)
        logger.info("Ingesting %s: %s chars, %s chunks.", filename, len(text), len(chunks))

        vectors = self.embeddings.embed(chunks) if chunks else []

        db = session_scope()
        try:
            document = Document(filename=filename, content_type=content_type, char_count=len(text))
            db.add(document)
            db.flush()

            for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
                db.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        text=chunk,
                        embedding_json=json.dumps(vector),
                    )
                )

            db.commit()
            return DocumentSummary(
                id=document.id,
                filename=document.filename,
                content_type=document.content_type,
                char_count=document.char_count,
                chunk_count=len(chunks),
            )
        finally:
            db.close()

    def list_documents(self) -> list[DocumentSummary]:
        db = session_scope()
        try:
            documents = list(db.scalars(select(Document).order_by(Document.uploaded_at.desc())))
            summaries = []
            for document in documents:
                count = len(
                    list(
                        db.scalars(
                            select(DocumentChunk).where(DocumentChunk.document_id == document.id)
                        )
                    )
                )
                summaries.append(
                    DocumentSummary(
                        id=document.id,
                        filename=document.filename,
                        content_type=document.content_type,
                        char_count=document.char_count,
                        chunk_count=count,
                    )
                )
            return summaries
        finally:
            db.close()

    def delete_document(self, document_id: int) -> bool:
        db = session_scope()
        try:
            document = db.get(Document, document_id)
            if document is None:
                return False

            db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
            db.delete(document)
            db.commit()
            return True
        finally:
            db.close()

    def search(self, query: str, limit: int = 5) -> list[ScoredChunk]:
        """Semantic search across every ingested document chunk."""
        query_embedding = self.embeddings.embed_one(query)

        db = session_scope()
        try:
            rows = db.execute(
                select(
                    DocumentChunk.id,
                    DocumentChunk.document_id,
                    DocumentChunk.text,
                    DocumentChunk.embedding_json,
                )
            ).all()
        finally:
            db.close()

        candidates = [
            (chunk_id, document_id, text, json.loads(embedding_json))
            for chunk_id, document_id, text, embedding_json in rows
        ]
        return rank_chunks(query_embedding, candidates, limit=limit)

    def ask(self, question: str, limit: int = 5) -> RagAnswer:
        """Answer a question using retrieval-augmented generation over documents."""
        matches = self.search(question, limit=limit)
        if not matches:
            return RagAnswer(
                answer="I don't have any documents to search yet, Dr. Opara.", sources=[]
            )

        filenames = self._filenames_for(matches)
        excerpts = "\n\n".join(
            f"[{filenames[match.document_id]}]\n{match.text}" for match in matches
        )
        prompt = f"Question: {question}\n\nRetrieved excerpts:\n\n{excerpts}"

        answer = self.ai.ask(prompt, instructions=_RAG_INSTRUCTIONS)
        return RagAnswer(answer=answer, sources=sorted(set(filenames.values())))

    @staticmethod
    def _filenames_for(matches: list[ScoredChunk]) -> dict[int, str]:
        document_ids = {match.document_id for match in matches}
        db = session_scope()
        try:
            documents = db.scalars(select(Document).where(Document.id.in_(document_ids)))
            return {document.id: document.filename for document in documents}
        finally:
            db.close()
