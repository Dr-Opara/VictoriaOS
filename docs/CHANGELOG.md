# Changelog

## Sprint 3 — Voice Platform

- Added `backend/voice/vad.py`: numpy energy-based voice activity detection
  (speech/silence detection, end-pointing, interruption support).
- Extended `WakeWordDetector` with `strip_wake_word()` for cleaner command
  extraction after "Hello Victoria".
- Rebuilt `SpeechService` (`backend/voice/speech.py`) and `TextToSpeech`
  (`backend/voice/tts.py`) on the OpenAI audio APIs for real transcription
  and synthesis (previously hardcoded stubs).
- Rebuilt `VoiceEngine` (`backend/voice/engine.py`) with a `ConversationSession`
  state machine (sleeping/awake/speaking), a 15s silence timeout, and
  interruption handling; voice commands now flow through
  `VictoriaAssistant` → the same Context Builder path as text.
- Added `POST /voice/command` (audio in, spoken reply out) and
  `GET /voice/text` (text-driven debug entry point).
- Documented that audio-based speaker verification and the physical
  ReSpeaker integration remain stubs pending real enrollment audio and
  hardware — not something to fake without them.

## Sprint 2 — Memory + Executive Assistant

- Added SQLite persistence via SQLAlchemy 2.x (`backend/database/`):
  `database.py`, `base.py`, `models.py`, `migrations.py`. Tables:
  `ConversationHistory`, `UserPreference`, `Task`, `Memory`. Created
  automatically on startup.
- Upgraded `MemoryService` to persist to SQLite: `remember`, `recall`,
  `recent`, `search`, `forget`, `clear` — memory now survives restarts.
- Added `backend/core/context.py` (`ContextBuilder`): loads recent
  conversation history, preferences, and open tasks, and renders them into
  every GPT prompt. `VictoriaOrchestrator` is now the only caller of
  `AIGateway.ask()`.
- Added `backend/profile/profile.py` (`UserProfile`): permanent preferences
  ("remember my favorite airline is United", etc.) with a parser for the
  "remember my X is Y" command pattern.
- Fleshed out `backend/task/manager.py` (`TaskManager`) with create/complete
  /delete/list and `due_tasks()` for future scheduling, plus
  `backend/task/scheduler.py` (`TaskScheduler.check_due()`).
- `VictoriaOrchestrator` now handles "remember ..." and "what do you
  remember about me?" directly, and records every turn to
  `ConversationHistory`.
- Added request logging middleware (`backend/app.py`): timestamp, method,
  path, status, duration, model, and exception tracebacks.
- Added API endpoints: `GET /memory`, `POST /remember`, `POST /forget`,
  `GET /tasks`, `POST /tasks`, `POST /tasks/{id}/complete`,
  `DELETE /tasks/{id}`. Existing `/think` and Yahoo Mail routing verified
  unchanged (both now also record conversation history).
- Added a test suite (`tests/`) covering memory, tasks, profile, the
  context builder, and VAD/wake-word logic — 20 tests, all passing.
- Removed accidentally committed `__pycache__` files and the empty/unused
  `backend/database/connection.py`; runtime artifacts (`data/`, `logs/`,
  `*.db`) are now git-ignored.
