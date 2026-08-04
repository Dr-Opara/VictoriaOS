from backend.core.context import ContextBuilder
from backend.memory.service import MemoryService
from backend.profile.profile import UserProfile
from backend.task.manager import TaskManager


def test_context_includes_preferences_memories_and_tasks():
    UserProfile().set_preference("favorite airline", "United")
    MemoryService().remember("anniversary", "June 3rd")
    TaskManager().create_task("Draft quarterly report")

    context = ContextBuilder().build(session_id="test-session")

    assert context.preferences["favorite airline"] == "United"
    assert any("anniversary" in memory for memory in context.memories)
    assert "Draft quarterly report" in context.open_tasks


def test_record_turn_persists_conversation_history():
    builder = ContextBuilder()
    builder.record_turn("test-session", "hi", "hello Dr. Opara")

    context = builder.build(session_id="test-session")
    assert len(context.history) == 1
    assert context.history[0].user_message == "hi"


def test_prompt_includes_context_sections():
    UserProfile().set_preference("preferred airport", "IAH")
    context = ContextBuilder().build(session_id="test-session")

    prompt = context.to_prompt("what's my preferred airport?")

    assert "IAH" in prompt
    assert "what's my preferred airport?" in prompt
