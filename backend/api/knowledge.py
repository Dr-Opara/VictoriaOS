from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, UploadFile
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from backend.knowledge.documents import UnsupportedDocumentError
from backend.knowledge.manager import KnowledgeManager
from backend.security.audit import audit_log

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])
knowledge_manager = KnowledgeManager()


class AskRequest(BaseModel):
    question: str
    limit: int = 5


@router.post("/documents")
async def upload_document(file: UploadFile):
    """Ingest a document: extract text, chunk it, and embed each chunk."""
    content = await file.read()
    try:
        summary = await run_in_threadpool(
            knowledge_manager.ingest, file.filename, content, file.content_type or ""
        )
    except UnsupportedDocumentError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    audit_log("knowledge.ingest", f"filename={summary.filename!r} chunks={summary.chunk_count}")
    return asdict(summary)


@router.get("/documents")
async def list_documents():
    """List every ingested document."""
    summaries = await run_in_threadpool(knowledge_manager.list_documents)
    return {"documents": [asdict(summary) for summary in summaries]}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """Delete a document and its chunks."""
    deleted = await run_in_threadpool(knowledge_manager.delete_document, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")

    audit_log("knowledge.delete", f"id={document_id}")
    return {"status": "deleted", "id": document_id}


@router.get("/search")
async def search_documents(q: str = Query(...), limit: int = 5):
    """Semantic search across every ingested document."""
    matches = await run_in_threadpool(knowledge_manager.search, q, limit)
    return {
        "results": [
            {
                "chunk_id": match.chunk_id,
                "document_id": match.document_id,
                "text": match.text,
                "score": match.score,
            }
            for match in matches
        ]
    }


@router.post("/ask")
async def ask_documents(request: AskRequest):
    """Answer a question using retrieval-augmented generation over documents."""
    result = await run_in_threadpool(knowledge_manager.ask, request.question, request.limit)
    return {"answer": result.answer, "sources": result.sources}
