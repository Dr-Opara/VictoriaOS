from backend.memory.service import MemoryService


def test_remember_and_recall():
    memory = MemoryService()
    memory.remember("favorite color", "blue")

    results = memory.recall("favorite color")
    assert len(results) == 1
    assert results[0].value == "blue"


def test_recent_orders_newest_first():
    memory = MemoryService()
    memory.remember("first", "1")
    memory.remember("second", "2")

    recent = memory.recent(limit=2)
    assert [item.key for item in recent] == ["second", "first"]


def test_search_matches_key_or_value():
    memory = MemoryService()
    memory.remember("wife's birthday", "August 12")

    results = memory.search("birthday")
    assert len(results) == 1


def test_forget_removes_matching_entries():
    memory = MemoryService()
    memory.remember("temp", "value")
    assert memory.forget("temp") == 1
    assert memory.recall("temp") == []


def test_clear_removes_everything():
    memory = MemoryService()
    memory.remember("a", "1")
    memory.remember("b", "2")
    assert memory.clear() == 2
    assert memory.memories() == []


def test_memory_persists_across_service_instances():
    MemoryService().remember("persisted", "yes")
    assert MemoryService().recall("persisted")[0].value == "yes"
