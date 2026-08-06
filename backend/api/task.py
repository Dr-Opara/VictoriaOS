from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from backend.security.audit import audit_log
from backend.task.manager import TaskManager
from backend.task.planner import TaskPlanner

router = APIRouter(tags=["Tasks"])
task_manager = TaskManager()
task_planner = TaskPlanner(manager=task_manager)


class CreateTaskRequest(BaseModel):
    title: str
    description: str = ""


def _serialize(task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
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
    audit_log("task.create", f"id={task.id} title={task.title!r}")
    return _serialize(task)


@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int):
    """Mark a task as completed."""
    task = task_manager.complete_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    audit_log("task.complete", f"id={task.id}")
    return _serialize(task)


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    """Delete a task."""
    if not task_manager.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found.")

    audit_log("task.delete", f"id={task_id}")
    return {"status": "deleted", "id": task_id}


@router.post("/tasks/prioritize")
async def prioritize_tasks():
    """Run AI prioritization over all pending tasks and persist the result."""
    plans = await run_in_threadpool(task_planner.prioritize)
    audit_log("task.prioritize", f"count={len(plans)}")
    return {
        "plans": [
            {"task_id": plan.task_id, "priority": plan.priority, "follow_up": plan.follow_up}
            for plan in plans
        ]
    }
