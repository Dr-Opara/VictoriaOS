from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.memory.service import MemoryService

router = APIRouter(tags=["Memory"])
memory_service = MemoryService()


class RememberRequest(BaseModel):
    key: str
    value: str


class ForgetRequest(BaseModel):
    key: str


@router.get("/memory")
def list_memory(query: str | None = None, limit: int = 20):
    """Return recent memories, optionally filtered by a search query."""
    memories = memory_service.search(query, limit=limit) if query else memory_service.recent(limit=limit)
    return {
        "memories": [
            {"key": memory.key, "value": memory.value, "created_at": memory.created_at}
            for memory in memories
        ]
    }


@router.post("/remember")
def remember(request: RememberRequest):
    """Store a new fact in Victoria's long-term memory."""
    memory = memory_service.remember(request.key, request.value)
    return {"status": "remembered", "key": memory.key, "value": memory.value}


@router.post("/forget")
def forget(request: ForgetRequest):
    """Delete every memory stored under the given key."""
    removed = memory_service.forget(request.key)
    return {"status": "forgotten", "key": request.key, "removed": removed}
