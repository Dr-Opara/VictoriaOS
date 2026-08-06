import json
from datetime import datetime, timedelta, timezone

from backend.task.manager import TaskManager
from backend.task.planner import TaskPlanner


class FakeAIGateway:
    def __init__(self, response: str):
        self.response = response
        self.calls = []

    def ask(self, prompt, instructions=None):
        self.calls.append(prompt)
        return self.response


def test_prioritize_applies_valid_gpt_response():
    manager = TaskManager()
    task = manager.create_task("Finish report")

    fake_response = json.dumps([{"id": task.id, "priority": "high", "follow_up": "Do it now."}])
    planner = TaskPlanner(manager=manager, ai=FakeAIGateway(fake_response))

    plans = planner.prioritize()

    assert plans[0].task_id == task.id
    assert plans[0].priority == "high"

    updated = manager.list_tasks(status="pending")[0]
    assert updated.priority == "high"


def test_prioritize_falls_back_on_invalid_json():
    manager = TaskManager()
    manager.create_task("Call the bank")

    planner = TaskPlanner(manager=manager, ai=FakeAIGateway("not valid json"))
    plans = planner.prioritize()

    assert len(plans) == 1
    assert plans[0].priority in {"high", "medium", "low"}


def test_prioritize_ignores_unknown_task_ids_and_falls_back():
    # A response with no valid task ids is treated the same as unusable
    # output: prioritize() falls back to the deterministic due-date plan
    # rather than silently leaving every task unprioritized.
    manager = TaskManager()
    task = manager.create_task("Real task")

    fake_response = json.dumps([{"id": 99999, "priority": "high", "follow_up": ""}])
    planner = TaskPlanner(manager=manager, ai=FakeAIGateway(fake_response))

    plans = planner.prioritize()

    assert len(plans) == 1
    assert plans[0].task_id == task.id

    updated = manager.list_tasks(status="pending")[0]
    assert updated.id == task.id
    assert updated.priority is not None


def test_prioritize_returns_empty_for_no_pending_tasks():
    manager = TaskManager()
    planner = TaskPlanner(manager=manager, ai=FakeAIGateway("[]"))

    assert planner.prioritize() == []


def test_fallback_plan_marks_overdue_as_high():
    manager = TaskManager()
    overdue = manager.create_task("Overdue", due_at=datetime.now(timezone.utc) - timedelta(days=1))
    future = manager.create_task("Far future", due_at=datetime.now(timezone.utc) + timedelta(days=30))
    no_due = manager.create_task("No due date")

    plans = TaskPlanner._fallback_plan([overdue, future, no_due])
    by_id = {plan.task_id: plan.priority for plan in plans}

    assert by_id[overdue.id] == "high"
    assert by_id[future.id] == "low"
    assert by_id[no_due.id] == "low"
