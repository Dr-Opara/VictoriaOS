# VictoriaOS Architecture

## Request flow

```
Voice / Text input
      |
      v
VictoriaAssistant.think()  (backend/core/assistant.py)
      |
      +-- email intent? -> EmailService (Yahoo IMAP)
      |
      v
VictoriaOrchestrator.process()  (backend/core/orchestrator.py)
      |
      +-- "remember ..."           -> UserProfile / MemoryService
      +-- "what do you remember?"  -> UserProfile + MemoryService summary
      |
      v
ContextBuilder.build()  (backend/core/context.py)
      |  loads: recent conversation history, preferences, open tasks, memories
      v
AIGateway.ask()  (backend/core/ai.py)  -> OpenAI Responses API
      |
      v
ContextBuilder.record_turn()  -> persists the exchange to ConversationHistory
```

**No endpoint calls the AI gateway directly.** `VictoriaOrchestrator` is the
only caller of `AIGateway.ask()`, and it always goes through `ContextBuilder`
first so every GPT request is grounded in what Victoria already knows.

## Persistence

SQLite via SQLAlchemy 2.x (`backend/database/`):

- `database.py` — engine, session factory, `get_db()`/`session_scope()`.
- `base.py` — shared `DeclarativeBase`.
- `models.py` — `ConversationHistory`, `UserPreference`, `Task`, `Memory`.
- `migrations.py` — `run_migrations()` creates any missing tables on startup
  (idempotent `create_all`; a full Alembic chain can replace this later if
  schema migrations beyond additive columns are needed).

The database file lives at `data/victoria.db` and is git-ignored — it is
runtime state, not source.

## Memory

`backend/memory/service.py` (`MemoryService`) implements `remember`,
`recall`, `recent`, `search`, `forget`, and `clear`, backed by the `Memory`
table via `backend/memory/store.py`. Memory persists across restarts because
it's just SQLite rows, not an in-process list.

## User profile / preferences

`backend/profile/profile.py` (`UserProfile`) stores permanent key/value
preferences (favorite airline, hotel chain, preferred airport, coffee order,
important dates, etc.) in the `UserPreference` table. It also parses
"remember my X is Y" commands into `(key, value)` pairs.

## Tasks

`backend/task/manager.py` (`TaskManager`) supports create/complete/delete/list
against the `Task` table, plus `due_tasks()` as a foundation for future
scheduling (a periodic job can poll this to proactively remind Dr. Opara).

## Voice pipeline

`backend/voice/`:

- `vad.py` — numpy energy-based voice activity detection: speech/silence
  detection and end-pointing (used to detect "the user stopped talking" and
  to detect interruptions while Victoria is speaking).
- `wakeword.py` — detects "Hello Victoria" in transcribed text.
- `speech.py` — STT via the OpenAI transcription API.
- `tts.py` — TTS via the OpenAI audio API (`synthesize`/`stream`).
- `speaker.py` — restricts responses to Dr. Opara. Text-based `authenticate()`
  is wired up; audio-based `verify_audio()` is an intentional stub — real
  voice-biometric verification needs an enrolled voiceprint and an embedding
  model, which requires actual enrollment audio from Dr. Opara to build
  safely and is not something to fake.
- `engine.py` — `VoiceEngine` ties it together: VAD -> STT -> wake word / an
  already-awake `ConversationSession` -> speaker check -> `VictoriaAssistant`
  (i.e. the same Context Builder path as text) -> TTS. `ConversationSession`
  tracks per-session state (`sleeping` / `awake` / `speaking`) so a user can
  have a multi-turn conversation without repeating the wake word, times out
  after 15s of silence, and supports interruption (new speech while Victoria
  is speaking cancels playback state).

`raspberry_pi/` holds the on-device microphone/speaker integration
points for the ReSpeaker array; those files are placeholders until real
hardware is wired up and tested on-device — that work cannot be validated
in this environment.

## Logging

`backend/core/logger.py` configures a shared `VictoriaOS` logger (console +
`logs/victoria.log`). `backend/app.py` adds an HTTP middleware that logs
every request's method, path, status, duration, and model, and logs
exceptions with a traceback before they propagate.

## System / observability endpoints

`backend/api/system.py` exposes what the dashboard (and any other client)
needs to observe the running system without touching the database or log
files directly: `GET /system/status` (uptime, version, environment, model),
`GET /system/usage` (conversation/memory/task counts), `GET /system/logs`
(tail of `logs/victoria.log`), and `GET /email/unread` (Yahoo Mail, reusing
`EmailService`).

## Executive Dashboard (`frontend/dashboard`)

Next.js 16 (App Router) + React 19 + TypeScript + Tailwind CSS 4, using
TanStack Query for data fetching/polling and Framer Motion for transitions.
Small hand-built UI primitives (`src/components/ui/`) follow the shadcn/ui
pattern (Radix primitives + `class-variance-authority` + `tailwind-merge`)
rather than depending on the `shadcn` CLI, since its interactive init flow
isn't scriptable non-interactively.

- `src/lib/api.ts` — typed fetch client for the backend; `NEXT_PUBLIC_API_URL`
  controls the target (defaults to `http://localhost:8000`).
- `src/components/providers.tsx` — wraps the app in `next-themes`
  (`defaultTheme="dark"`) and a `QueryClient`.
- `src/components/layout/` — `Sidebar` (desktop), `MobileNav` (bottom bar on
  small screens), `TopBar` (live online/offline status pill).
- Pages: `/` (overview), `/chat`, `/voice`, `/email`, `/memory`, `/tasks`,
  `/calendar`, `/weather`, `/usage`, `/logs`, `/settings`. Calendar and
  Weather intentionally render a "not connected" state — there is no backend
  integration for either yet (see roadmap), and faking data would be
  misleading.
- The `/voice` page uses the browser's native `SpeechRecognition` API for a
  local, always-available demo of live transcription; it is a UI convenience
  only. Production voice runs through the backend pipeline described above
  (`POST /voice/command`), not the browser API.
- "Real-time" updates are implemented as TanStack Query polling (5-30s
  intervals depending on the page) rather than WebSockets/SSE — a
  deliberately simpler choice for v1 that can be swapped for a push-based
  transport later without changing the page components' data-fetching shape.

CORS: `backend/config/settings.py` exposes `dashboard_origins` (defaults to
`http://localhost:3000`), applied via `CORSMiddleware` in `backend/app.py`.
