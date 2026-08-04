from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.task.manager import TaskManager

router = APIRouter(tags=["Tasks"])
task_manager = TaskManager()


class CreateTaskRequest(BaseModel):
    title: str
    description: str = ""


def _serialize(task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "due_at": task.due_at,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
    }


@router.get("/tasks")
def list_tasks(status: str | None = None):
    """List Victoria's tasks, optionally filtered by status."""
    return {"tasks": [_serialize(task) for task in task_manager.list_tasks(status=status)]}


@router.post("/tasks")
def create_task(request: CreateTaskRequest):
    """Create a new task for Victoria to track."""
    task = task_manager.create_task(request.title, request.description)
    return _serialize(task)


@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int):
    """Mark a task as completed."""
    task = task_manager.complete_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    return _serialize(task)


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    """Delete a task."""
    if not task_manager.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found.")

    return {"status": "deleted", "id": task_id}
