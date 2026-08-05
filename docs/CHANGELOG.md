# Changelog

## Sprint 14/15 — Security + Production

- Added `backend/security/`: `ApiKeyMiddleware` (shared-secret auth via
  `X-API-Key`, appropriate for a single-user assistant rather than full
  OAuth/JWT accounts), `RateLimitMiddleware` (in-memory sliding window),
  `SecurityHeadersMiddleware` (nosniff/frame-options/referrer-policy/
  permissions-policy, HSTS when behind HTTPS), and `audit.py` (a dedicated
  `logs/audit.log` for memory/task mutations).
- New settings: `API_KEY`, `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`.
- Added Docker support: `docker/backend.Dockerfile`, `docker/frontend.Dockerfile`
  (Next.js standalone output), `docker/nginx.conf` reverse proxy, and a
  filled-in `docker-compose.yml` (backend + frontend + nginx, named volumes
  for SQLite data/logs, backend healthcheck). **Not built/verified in this
  environment** — no Docker daemon was available; run `docker compose up`
  and smoke-test before relying on it.
- Added `.github/workflows/ci.yml`: backend (ruff, pytest, import-boot
  check) and frontend (lint, build) as separate jobs on every push/PR to
  `main`.
- Added `scripts/backup_db.py`: SQLite online-backup copy with retention
  pruning; nothing schedules it yet (needs a host-level cron/Task
  Scheduler/systemd timer).
- Verified: 28/28 backend tests pass (5 new, covering the security
  middleware and the backup script), `ruff check .` clean across the whole
  repo, app still boots and CORS/API-key/rate-limit behavior confirmed live
  against a running server.

## Sprint 4 — Executive Dashboard

- Scaffolded `frontend/dashboard`: Next.js 16 (App Router, Turbopack) +
  React 19 + TypeScript + Tailwind CSS 4 (installed "latest" rather than the
  requested Next 15, since 16 was current stable at scaffold time).
- Added TanStack Query, Framer Motion, `next-themes` (dark mode by default),
  and hand-built shadcn/ui-style primitives (Button, Card, Badge, Input,
  Textarea) on top of Radix + `class-variance-authority` — the `shadcn` CLI's
  `init` wizard couldn't be driven non-interactively, so the primitives were
  authored directly instead of skipped.
- Pages: Overview, Chat, Voice (browser STT demo), Email, Memory, Tasks,
  Calendar, Weather, AI Usage, Logs, Settings — sidebar nav on desktop,
  bottom nav on mobile.
- Added backend endpoints the dashboard needed: `GET /system/status`,
  `GET /system/usage`, `GET /system/logs`, `GET /email/unread`
  (`backend/api/system.py`), plus CORS middleware
  (`Settings.dashboard_origins`) so the dashboard can call the API from
  `localhost:3000`.
- Calendar and Weather pages honestly show a "not connected" state rather
  than fabricated data — neither has a backend integration yet (both need
  external OAuth/API credentials, tracked in the roadmap).
- Verified: `npm run lint` and `npm run build` both clean; backend serves
  the new endpoints correctly with CORS preflight verified via curl; all 20
  backend tests still pass; `database.py`/`migrations.py` were reconciled
  after a manual edit (added `init_database()`) without changing behavior.

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
