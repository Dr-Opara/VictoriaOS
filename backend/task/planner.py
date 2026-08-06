from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from backend.core.ai import AIGateway
from backend.core.logger import logger
from backend.database.models import Task
from backend.task.manager import TaskManager

_VALID_PRIORITIES = {"high", "medium", "low"}

_PLANNER_INSTRUCTIONS = """
You are Victoria's task-prioritization engine. You will be given Dr.
Opara's pending tasks as JSON. Assign each one a priority of "high",
"medium", or "low" based on urgency (due date proximity), apparent
importance, and dependencies between tasks. Also write one short,
actionable follow-up suggestion per task.

Respond with ONLY a JSON array, no prose, no markdown fences, in this
exact shape:

[{"id": 1, "priority": "high", "follow_up": "..."}]
""".strip()


@dataclass(frozen=True, slots=True)
class TaskPlan:
    task_id: int
    priority: str
    follow_up: str


class TaskPlanner:
    """AI-driven task prioritization: the "intelligent" half of TaskManager.

    Deliberately kept separate from ``TaskManager`` (which stays a plain
    CRUD layer with no GPT dependency) so task storage works even without
    an OpenAI key configured, and so this class can be tested/mocked in
    isolation from persistence.
    """

    def __init__(self, manager: TaskManager | None = None, ai: AIGateway | None = None) -> None:
        self.manager = manager or TaskManager()
        self.ai = ai or AIGateway()

    def prioritize(self, apply: bool = True) -> list[TaskPlan]:
        """Ask GPT to prioritize all pending tasks, optionally persisting the result."""
        pending = self.manager.list_tasks(status="pending")
        if not pending:
            return []

        prompt = self._build_prompt(pending)

        try:
            raw_response = self.ai.ask(prompt, instructions=_PLANNER_INSTRUCTIONS)
            plans = self._parse_response(raw_response, valid_ids={task.id for task in pending})
        except Exception:
            logger.exception("Task prioritization GPT call failed.")
            plans = []

        if not plans:
            plans = self._fallback_plan(pending)

        if apply:
            for plan in plans:
                self.manager.set_priority(plan.task_id, plan.priority)

        return plans

    @staticmethod
    def _build_prompt(tasks: list[Task]) -> str:
        payload = [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "due_at": task.due_at.isoformat() if task.due_at else None,
            }
            for task in tasks
        ]
        return json.dumps(payload)

    @staticmethod
    def _parse_response(raw_response: str, valid_ids: set[int]) -> list[TaskPlan]:
        text = raw_response.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Task planner returned non-JSON output; using fallback plan.")
            return []

        plans: list[TaskPlan] = []
        for item in parsed:
            task_id = item.get("id")
            priority = item.get("priority", "medium")
            if task_id not in valid_ids or priority not in _VALID_PRIORITIES:
                continue
            plans.append(
                TaskPlan(task_id=task_id, priority=priority, follow_up=item.get("follow_up", ""))
            )

        return plans

    @staticmethod
    def _fallback_plan(tasks: list[Task]) -> list[TaskPlan]:
        """Deterministic priority-by-due-date, used if GPT is unavailable."""
        now = datetime.now(timezone.utc)
        plans = []
        for task in tasks:
            due_at = task.due_at
            if due_at is not None and due_at.tzinfo is None:
                # SQLite drops tzinfo on round-trip; every stored timestamp
                # in this codebase is written as UTC (see _utcnow()), so a
                # naive value read back can be safely treated as UTC.
                due_at = due_at.replace(tzinfo=timezone.utc)

            if due_at is None:
                priority = "low"
            elif due_at <= now:
                priority = "high"
            elif (due_at - now).days <= 2:
                priority = "medium"
            else:
                priority = "low"
            plans.append(TaskPlan(task_id=task.id, priority=priority, follow_up=""))

        return plans
