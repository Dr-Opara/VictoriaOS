from backend.task.manager import TaskManager


def test_create_and_list_task():
    manager = TaskManager()
    manager.create_task("Book flight", "United to IAH")

    tasks = manager.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].title == "Book flight"
    assert tasks[0].status == "pending"


def test_complete_task():
    manager = TaskManager()
    task = manager.create_task("Call dentist")

    completed = manager.complete_task(task.id)
    assert completed.status == "completed"
    assert completed.completed_at is not None

    assert manager.list_tasks(status="pending") == []


def test_complete_missing_task_returns_none():
    manager = TaskManager()
    assert manager.complete_task(999) is None


def test_delete_task():
    manager = TaskManager()
    task = manager.create_task("Temp task")

    assert manager.delete_task(task.id) is True
    assert manager.delete_task(task.id) is False
