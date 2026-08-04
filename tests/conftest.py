import os
import tempfile

import pytest

_tmp_dir = tempfile.mkdtemp(prefix="victoriaos-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp_dir, 'test.db').replace(os.sep, '/')}"
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from backend.config.settings import get_settings  # noqa: E402

get_settings.cache_clear()

from backend.database.migrations import run_migrations  # noqa: E402

run_migrations()


@pytest.fixture(autouse=True)
def _clean_database():
    """Reset all tables between tests so they stay isolated."""
    from sqlalchemy import delete

    from backend.database.database import session_scope
    from backend.database.models import ConversationHistory, Memory, Task, UserPreference

    yield

    db = session_scope()
    try:
        for model in (ConversationHistory, Memory, Task, UserPreference):
            db.execute(delete(model))
        db.commit()
    finally:
        db.close()
