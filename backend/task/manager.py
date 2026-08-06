from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from backend.database.database import session_scope
from backend.database.models import Task


class TaskManager:
    """Create, complete, delete, and list tasks Victoria is tracking."""

    def create_task(
        self, title: str, description: str = "", due_at: datetime | None = None
    ) -> Task:
        """Create a new pending task."""
        db = session_scope()
        try:
            task = Task(title=title.strip(), description=description.strip(), due_at=due_at)
            db.add(task)
            db.commit()
            db.refresh(task)
            return task
        finally:
            db.close()

    def complete_task(self, task_id: int) -> Task | None:
        """Mark a task as completed. Returns ``None`` if it does not exist."""
        db = session_scope()
        try:
            task = db.get(Task, task_id)
            if task is None:
                return None

            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(task)
            return task
        finally:
            db.close()

    def delete_task(self, task_id: int) -> bool:
        """Delete a task by id. Returns ``True`` if it was found and removed."""
        db = session_scope()
        try:
            task = db.get(Task, task_id)
            if task is None:
                return False

            db.delete(task)
            db.commit()
            return True
        finally:
            db.close()

    def list_tasks(self, status: str | None = None) -> list[Task]:
        """List tasks, optionally filtered by status (``pending``/``completed``)."""
        db = session_scope()
        try:
            statement = select(Task).order_by(Task.created_at.desc())
            if status:
                statement = statement.where(Task.status == status)

            return list(db.scalars(statement))
        finally:
            db.close()

    def set_priority(self, task_id: int, priority: str) -> Task | None:
        """Set a task's priority (``high``/``medium``/``low``)."""
        db = session_scope()
        try:
            task = db.get(Task, task_id)
            if task is None:
                return None

            task.priority = priority
            db.commit()
            db.refresh(task)
            return task
        finally:
            db.close()

    def due_tasks(self, now: datetime | None = None) -> list[Task]:
        """Return pending tasks whose due date has passed, for future scheduling."""
        reference_time = now or datetime.now(timezone.utc)
        db = session_scope()
        try:
            statement = (
                select(Task)
                .where(Task.status == "pending")
                .where(Task.due_at.is_not(None))
                .where(Task.due_at <= reference_time)
                .order_by(Task.due_at.asc())
            )
            return list(db.scalars(statement))
        finally:
            db.close()
