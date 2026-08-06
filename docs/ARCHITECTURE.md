# VictoriaOS Architecture

## Request flow

```
Voice / Text input
      |
      v
VictoriaAssistant.think()  (backend/core/assistant.py)
      |
      +-- email intent?     -> EmailService (Yahoo IMAP)
      +-- knowledge intent? -> KnowledgeManager.ask() (RAG over documents)
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
`backend/task/planner.py` (`TaskPlanner`) is the GPT-driven layer on top:
`prioritize()` asks GPT-5 to rank pending tasks and suggest a follow-up per
task, falling back to a deterministic due-date heuristic if GPT is
unavailable or returns something unparseable - either way the result is
always persisted via `TaskManager.set_priority()`.

## Calendar

`backend/integrations/calendar/` follows the same provider/manager/service
shape as email: `LocalCalendarProvider` (SQLite-backed, always available,
no external credentials) does the real work; `GoogleCalendarProvider` is a
documented stub that raises `CalendarConfigurationError` until a real
Google Cloud OAuth app is registered. `CalendarService` is what callers
(the briefing, the API, eventually voice commands) actually use, so
swapping providers later doesn't touch call sites.

## Weather

`backend/integrations/weather/service.py` (`WeatherService`) wraps
OpenWeatherMap, gated behind `WEATHER_API_KEY`/`WEATHER_LOCATION` - the
same "gracefully disabled, never faked" pattern as wake-word detection and
speaker verification elsewhere in this codebase.

## Daily Briefing

`backend/core/briefing.py` (`DailyBriefingService`) is the executive
summary layer: `gather_context()` pulls real data from calendar, weather,
email, tasks, and system settings (each failing/missing source is skipped,
not faked), then `generate()` hands that context to GPT-5 to produce a
short, spoken-style briefing with a personalized greeting.
`generate_audio()` runs it through TTS. `GET /briefing` and
`GET /briefing/voice` expose this.

## Knowledge Engine (RAG)

`backend/knowledge/`:

- `documents.py` — text extraction by file type (.txt/.md/.csv, .pdf via
  `pypdf`, .docx via `python-docx`, .pptx via `python-pptx`, .xlsx via
  `openpyxl`, images via `pytesseract` OCR when the Tesseract binary is
  actually installed on the host - a clear error otherwise) plus
  fixed-size chunking with overlap.
- `embeddings.py` — `EmbeddingService` wraps the OpenAI embeddings API
  (`text-embedding-3-small` by default).
- `search.py` — brute-force cosine-similarity ranking over every stored
  chunk. Appropriate for a personal knowledge base's scale; a real vector
  index (FAISS/pgvector) is the natural upgrade if the corpus grows large,
  tracked in the roadmap rather than built preemptively.
- `manager.py` — `KnowledgeManager` ties it together: `ingest()` (extract →
  chunk → embed → store), `search()` (semantic search), `ask()`
  (retrieval-augmented generation: search, then GPT-5 answers using only
  the retrieved excerpts, citing filenames).
- New tables: `Document`, `DocumentChunk` (embedding stored as a JSON
  float array - no vector column type needed at this scale).
- `VictoriaAssistant` routes "my documents/files/notes"-shaped questions
  here automatically (see the request-flow diagram above) - this is
  VictoriaOS's long-term document memory, distinct from but reachable
  through the same conversational surface as `MemoryService`'s short facts.

## Voice pipeline

VictoriaOS's voice pipeline is split across two machines — see
[docs/VOICE_PIPELINE.md](VOICE_PIPELINE.md) for the full protocol and
sequence diagram. Summary:

**Mini PC** (`backend/voice/`) — all AI/audio-processing capability lives
here; the Pi never calls OpenAI directly:

- `vad.py` — numpy energy-based voice activity detection: speech/silence
  detection and end-pointing (used to detect "the user stopped talking" and
  to detect interruptions while Victoria is speaking).
- `wakeword.py` — detects "Hello Victoria" in transcribed text.
- `speech.py` — STT via the OpenAI transcription API.
- `tts.py` — TTS via the OpenAI audio API (`synthesize`/`stream`); supports
  `response_format="wav"` for codec-free playback on the Pi.
- `speaker.py` — restricts responses to Dr. Opara. `verify_audio()` is fully
  wired into the pipeline but gated behind `is_enrolled()`: real
  voice-biometric verification needs an enrolled voiceprint and an embedding
  model, which requires actual enrollment audio from Dr. Opara to build
  safely, so it's skipped (not faked) until one exists.
- `engine.py` — `VoiceEngine` ties it together: VAD -> speaker check -> STT
  -> wake word / an already-awake `ConversationSession` -> `VictoriaAssistant`
  (i.e. the same Context Builder path as text) -> TTS. `ConversationSession`
  tracks per-session state (`sleeping` / `awake` / `speaking`) so a user can
  have a multi-turn conversation without repeating the wake word, times out
  after 15s of silence, and supports interruption.
- `backend/api/voice.py` exposes this over HTTP/WS: `GET /voice/connect`
  (handshake), `WS /voice/stream` (chunked audio in, JSON result + WAV audio
  out, end-of-turn framed), `POST /voice/transcribe` (STT only),
  `POST /voice/respond` (text in, spoken reply out — no wake-word gate).

**Raspberry Pi** (`raspberry_pi/`) — the "voice node": microphone capture,
local wake-word detection (or VAD fallback), and speaker playback, talking
to the Mini PC exclusively through `/voice/*`:

- `audio/devices.py` — runtime device discovery/selection by name hint,
  never a hardcoded index.
- `audio/microphone.py`, `audio/speaker.py` — capture/playback via
  `sounddevice`.
- `audio/vad.py` — a small, intentionally independent re-implementation of
  the same energy-VAD technique (the Pi's venv must not depend on the
  Mini PC's full backend package).
- `audio/diagnostics.py` — device report + live input-level check
  (`python -m raspberry_pi.audio.diagnostics`).
- `wakeword/` — pluggable `WakeWordEngine` interface;
  `OpenWakeWordEngine` loads a trained model if `WAKE_WORD_MODEL_PATH` is
  configured, otherwise `NullWakeWordEngine` disables local detection and
  the node falls back to VAD-triggered turns gated server-side.
- `client/connection.py` — `MiniPCClient` (REST) and `VoiceStreamClient`
  (WS, sync client, reconnect-with-backoff).
- `client/voice_node.py` — the orchestrator; run directly or via the
  provided systemd unit (`systemd/victoria-voice.service`).
- `health/monitor.py` — heartbeat polling of the Mini PC and local
  mic/speaker availability, logging state transitions.

## Logging

`backend/core/logger.py` configures a shared `VictoriaOS` logger (console +
`logs/victoria.log`). `backend/app.py` adds an HTTP middleware that logs
every request's method, path, status, duration, and model, and logs
exceptions with a traceback before they propagate.

## Security (`backend/security/`)

VictoriaOS is a single-user (Dr. Opara) assistant, not a multi-tenant
service — the security model is scoped to that threat model rather than
building out full OAuth/JWT user accounts and RBAC for one user:

- `api_key.py` (`ApiKeyMiddleware`) — when `API_KEY` is set, every request
  except `/health` and the docs routes must send a matching `X-API-Key`
  header. Unset in local dev (logs one warning, stays open) so `uvicorn
  --reload` keeps working without ceremony; **must** be set before exposing
  the API beyond localhost.
- `rate_limit.py` (`RateLimitMiddleware`) — in-memory sliding-window limiter
  keyed by client IP (`RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS`,
  default 120/60s). In-process by design; a multi-instance deployment would
  swap in a Redis-backed limiter behind the same interface.
- `headers.py` (`SecurityHeadersMiddleware`) — `X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` on every
  response; `Strict-Transport-Security` is added only when the request
  arrived over HTTPS (or `X-Forwarded-Proto: https`) so plain HTTP access
  during local dev is never broken by HSTS.
- `audit.py` (`audit_log`) — a separate `logs/audit.log`, written to from
  the memory (`remember`/`forget`) and task (`create`/`complete`/`delete`)
  endpoints — sensitive mutations get their own trail independent of the
  general request log.

Middleware order in `backend/app.py` (outermost to innermost on the
request): security headers -> rate limit -> API key -> CORS -> request
logging -> route handler.

## Deployment (`docker/`, `docker-compose.yml`, `.github/workflows/ci.yml`)

- `docker/backend.Dockerfile` — slim Python image, non-root user, container
  healthcheck against `/health`.
- `docker/frontend.Dockerfile` — multi-stage Node build using Next.js
  `output: "standalone"` (set in `next.config.ts`), non-root runtime user.
- `docker-compose.yml` — `backend` + `frontend` + an `nginx` reverse proxy
  (`docker/nginx.conf`) that routes `/api/*` to the backend and everything
  else to the dashboard; the backend's SQLite data and logs live in named
  volumes so they survive container recreation. TLS termination has a home
  in the nginx config but no certificate is generated — that needs a real
  domain.
- `.github/workflows/ci.yml` — on every push/PR to `main`: backend
  (`ruff check backend`, `pytest`, import-boot check) and frontend
  (`npm run lint`, `npm run build`) run as separate jobs.
- `scripts/backup_db.py` — SQLite online-backup API copy of `data/victoria.db`
  into `backups/`, with retention pruning (`--keep`, default 14). Nothing
  schedules it yet; run it from cron/Task Scheduler/a systemd timer on
  whatever host runs the backend.

The Docker images have not been built in this environment (no Docker daemon
available here) — build and run `docker compose up` at least once before
depending on them for a real deployment.

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

**Design system**: an original "dark luxury" theme — near-black background
with a subtle radial cyan glow, glassmorphism panels (`.glass`/
`.glass-strong` utility classes in `globals.css`: `backdrop-filter: blur()`
+ a hairline cyan-tinted border), and an electric-cyan accent
(`--accent`/`--accent-strong`) used sparingly for focus states, active nav,
and emphasis glows (`.glow-cyan`). All colors are CSS custom properties so
the existing light/dark toggle (`next-themes`) still works — light mode
swaps the same variables to a bright, high-contrast palette rather than
being a separate theme. Not modeled on any specific existing product.

- `src/lib/api.ts` — typed fetch client for the backend; `NEXT_PUBLIC_API_URL`
  controls the target (defaults to `http://localhost:8000`), and
  `NEXT_PUBLIC_API_KEY` is sent as `X-API-Key` when the backend has one set.
- `src/components/providers.tsx` — wraps the app in `next-themes`
  (`defaultTheme="dark"`), a `QueryClient`, and `ToastProvider`.
- `src/components/ai-core/ai-core.tsx` — the animated AI Core: an original
  concentric-rings-plus-waveform visual (not modeled on any specific
  existing assistant UI) with six distinct Framer Motion states (`idle`,
  `listening`, `thinking`, `speaking`, `offline`, `error`), each with its
  own animation/color; respects `prefers-reduced-motion`.
- `src/components/ui/toast.tsx`, `state.tsx` — shared notification system
  and `LoadingState`/`ErrorState`/`EmptyState` components reused across
  every page for consistent loading/empty/error handling.
- `src/components/layout/` — `Sidebar` (desktop, glass panel), `MobileNav`
  (bottom bar, a curated 5-item subset on small screens), `TopBar` (live
  online/offline status pill). A skip-to-content link in the root layout
  covers keyboard/screen-reader navigation.
- Pages (exactly seven, per spec): `/` (Home — briefing, calendar, weather,
  and stats widgets), `/assistant` (chat merged with the AI Core and a
  browser-`SpeechRecognition` voice-input toggle), `/memory`, `/knowledge`
  (new — document upload, semantic search, RAG Q&A), `/tasks` (now with
  priority badges and a "Prioritize with AI" action), `/email`, `/settings`
  (now also folds in AI usage stats and a live log tail, previously
  separate pages). Calendar/weather/voice/usage/logs are no longer
  top-level routes — their functionality was consolidated into Home,
  Assistant, and Settings rather than left as dead pages.
- Production voice still runs through the backend pipeline
  (`POST /voice/command`, `WS /voice/stream`); the Assistant page's
  microphone toggle is a browser-only convenience for dictating chat input,
  not a second voice pipeline.
- "Real-time" updates are implemented as TanStack Query polling (5-60s
  intervals depending on the page) rather than WebSockets/SSE — a
  deliberately simpler choice for v1 that can be swapped for a push-based
  transport later without changing the page components' data-fetching shape.

CORS: `backend/config/settings.py` exposes `dashboard_origins` (defaults to
`http://localhost:3000`), applied via `CORSMiddleware` in `backend/app.py`.
