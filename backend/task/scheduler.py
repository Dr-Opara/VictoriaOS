from __future__ import annotations

from backend.core.logger import logger
from backend.task.manager import TaskManager


class TaskScheduler:
    """Polls for due tasks so Victoria can proactively surface them.

    This is a lightweight foundation for future scheduling: a periodic job
    (cron, APScheduler, or a background asyncio task) can call ``check_due``
    to get tasks that need attention right now.
    """

    def __init__(self, manager: TaskManager | None = None) -> None:
        self.manager = manager or TaskManager()

    def check_due(self) -> list[str]:
        """Return human-readable reminders for tasks that are now due."""
        due = self.manager.due_tasks()
        if due:
            logger.info("TaskScheduler found %s due task(s).", len(due))

        return [f"Reminder: '{task.title}' is due." for task in due]
