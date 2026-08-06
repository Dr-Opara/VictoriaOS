# Changelog

## v0.2 Runtime Release (`release/v0.2-runtime`)

Scope: `backend/`, `raspberry_pi/`, `tests/`, Docker/runtime deployment
files only. No new integrations, no login/auth, `frontend/` untouched. See
`docs/PROJECT_STATUS.md` for the full acceptance-criteria breakdown.

**Real bug fixed**: `WS /voice/stream` sent raw headerless PCM straight to
`VoiceEngine.process_audio()` without marking it as such, so it would have
gone to OpenAI's transcription API without a valid audio container -
untested and would not have worked on real hardware. Fixed with
`backend/voice/audio_format.py` (PCM→WAV wrapping, matching what
`GET /voice/connect` advertises) and a new `input_format` parameter on
`process_audio()`. Also fixed: the energy-based VAD was being run on
arbitrary uploaded file bytes (`/voice/command`) as if they were raw PCM,
which misinterprets WAV headers/compressed audio as sample data - VAD now
only runs on genuinely raw PCM (the WS path); file uploads rely on STT
returning an empty transcript to detect silence instead.

**Audio subsystem** (`raspberry_pi/audio/`): `Microphone`/`Speaker` now
raise `MicrophoneDisconnectedError`/`SpeakerDisconnectedError` when the
underlying PortAudio stream stops unexpectedly (unplugged device, driver
crash) instead of hanging forever or silently doing nothing - the voice
node catches these specifically, logs clearly, and retries device
selection with backoff. Added ambient-noise calibration
(`diagnostics.py --calibrate-noise`) that recommends a `VAD_ENERGY_THRESHOLD`
for the room's actual background noise.

**Wake word**: added a push-to-talk test mode (`PUSH_TO_TALK=true`,
`raspberry_pi/client/push_to_talk.py`) - press Enter in an interactive
terminal to start a turn, for exercising the full pipeline on hardware
without a trained wake-word model. Startup logging now clearly states
which of the three listening strategies (local wake word / push-to-talk /
VAD-fallback) is active and why.

**Playback**: `Speaker` now prevents overlapping playback (starting a new
clip stops any clip already playing) and supports interruption - the
voice node plays replies non-blocking and stops playback immediately if
the VAD detects the user talking during it, then drains stale buffered
audio before the next turn.

**Mini PC runtime**: added `scripts/start_mini_pc.ps1` - one PowerShell
command that validates required env vars (presence only, never prints
values), checks/offers to create a Windows Firewall rule, prints the
LAN address(es) for the Pi's `MINI_PC_URL`, and starts uvicorn bound to
`0.0.0.0`.

**Pi systemd service**: unit file now logs to the systemd journal
(`journalctl -u victoria-voice.service`) instead of raw append files, sets
`PYTHONUNBUFFERED=1`, and documents install/start/stop/restart/status/log
commands in `docs/DEPLOYMENT.md`.

**Testing**: added `tests/test_voice_api.py` (12 tests covering
`/voice/connect`, `/voice/transcribe`, `/voice/respond`, `/voice/command`,
and the WS stream's connect/ping-pong/end-of-turn/API-key-rejection
behavior, all with mocked STT/GPT/TTS so they don't require live OpenAI
access) and `tests/raspberry_pi/test_diagnostics.py` (7 tests covering
input-level measurement, noise calibration, and graceful backend-
unavailable/no-devices reporting via a fake `sounddevice` backend). 103
tests total, all passing. `ruff check` clean; `mypy` clean on
`backend/voice`, `backend/api/voice.py`, and `raspberry_pi` (pre-existing,
unrelated findings in `backend/integrations/email/yahoo.py` left
untouched, out of scope). `docker compose config --quiet` validates the
compose file without a daemon.

**Docs**: rewrote `docs/DEPLOYMENT.md` (PowerShell launch command,
firewall/LAN binding, mic/speaker/noise-calibration setup, systemd
commands, a troubleshooting table), updated `docs/VOICE_PIPELINE.md`
(three listening strategies, disconnect handling, interruption, honest
verified-vs-hardware-blocked status), and added `docs/PROJECT_STATUS.md`
(acceptance-criteria-by-criteria status: passed / ready for hardware
validation / blocked by missing device or model - never claiming untested
hardware functionality as passing).

## Dashboard Redesign — Dark Luxury / Glassmorphism

- New original visual design (not modeled on any existing product):
  near-black background with a radial cyan glow, glassmorphism panels
  (`.glass`/`.glass-strong`), electric-cyan accent used for focus/active/
  emphasis states. Implemented as CSS custom properties in `globals.css`
  so the existing light/dark toggle keeps working against the same tokens.
- New `AICore` component (`src/components/ai-core/`): an animated visual
  with six distinct states (idle/listening/thinking/speaking/offline/
  error), each with its own Framer Motion animation and color; respects
  `prefers-reduced-motion`. Shown on Home (system status) and Assistant
  (conversation state).
- New shared components: `ToastProvider`/`useToast` (notification system)
  and `LoadingState`/`ErrorState`/`EmptyState` (consistent loading/empty/
  error handling), used across every page.
- Restructured to exactly the seven requested pages: `/` (Home),
  `/assistant`, `/memory`, `/knowledge` (new), `/tasks`, `/email`,
  `/settings`. Voice, Calendar, Weather, AI Usage, and Logs are no longer
  separate top-level pages - their real functionality was folded into
  Home (calendar/weather widgets, executive briefing), Assistant (voice
  input via the AI Core), and Settings (usage stats, live log tail) rather
  than deleted or left as dead routes.
- New Knowledge page: upload documents, ask questions (RAG), browse/delete
  ingested documents - wired to the `/knowledge/*` endpoints added in the
  Executive Intelligence layer below.
- Tasks page: priority badges (color-coded by high/medium/low) and a
  "Prioritize with AI" action wired to `POST /tasks/prioritize`.
- Accessibility: a skip-to-content link, `aria-label`/`aria-pressed` on
  icon-only and toggle controls, `prefers-reduced-motion` support, and
  focus-visible rings using the accent color for keyboard navigation.
- `src/lib/api.ts` extended with typed clients for calendar, weather,
  briefing, and knowledge; optional `NEXT_PUBLIC_API_KEY` support for
  deployments where the backend's `API_KEY` is set.
- Verified: `npm run lint` and `npm run build` both clean, producing
  exactly the seven expected routes; all 7 pages return 200 against a live
  backend; CORS preflight verified to correctly allow the configured
  dashboard origin and reject an unlisted one.

## Executive Intelligence Layer

- **Daily Briefing** (`backend/core/briefing.py`, `GET /briefing`,
  `GET /briefing/voice`): gathers real data from every subsystem (time,
  local calendar, weather if configured, unread email count, pending/
  overdue tasks, system status) and has GPT-5 turn it into a spoken-style
  briefing with a personalized greeting. Each section degrades gracefully
  and silently when its data source isn't configured (no calendar events,
  no weather key, Yahoo Mail not configured) rather than erroring.
- **Calendar** (`backend/integrations/calendar/`): a real, working local
  calendar (`LocalCalendarProvider`, SQLite-backed) - create/reschedule/
  cancel/list today's & upcoming events - behind the same
  provider/manager pattern as email, so a `GoogleCalendarProvider` can
  be dropped in later without changing call sites. Google Calendar itself
  is a documented stub that raises a clear configuration error (needs a
  registered OAuth app this environment doesn't have) rather than faking
  sync. New `GET/POST/PATCH/DELETE /calendar/*` endpoints.
- **Weather** (`backend/integrations/weather/`): OpenWeatherMap client,
  gated behind `WEATHER_API_KEY`/`WEATHER_LOCATION` exactly like the other
  optional integrations in this codebase - `GET /weather/current` reports
  `{"configured": false}` rather than fabricating conditions when unset.
- **Intelligent Task Manager** (`backend/task/planner.py`,
  `POST /tasks/prioritize`): GPT-driven prioritization (high/medium/low +
  a one-line follow-up per task) with a deterministic due-date-based
  fallback when GPT is unavailable or returns unusable output. Added a
  `priority` column to `Task` via a new lightweight additive-column
  migration path in `migrations.py` (SQLite's `create_all` never alters
  existing tables).
- **Knowledge Engine / RAG** (`backend/knowledge/`): document ingestion
  (`.txt/.md/.csv`, `.pdf`, `.docx`, `.pptx`, `.xlsx`, and OCR for images
  when the Tesseract binary is installed - a clear error otherwise, not
  silently empty text) → chunking → OpenAI embeddings → brute-force cosine
  similarity search → GPT-5 answer synthesis with cited sources. New
  `Document`/`DocumentChunk` tables, `POST/GET/DELETE /knowledge/documents`,
  `GET /knowledge/search`, `POST /knowledge/ask`.
- **Long-term memory integration**: `VictoriaAssistant` now routes
  "my documents/files/notes"-style questions to the Knowledge Engine (RAG)
  the same way it already routes email-check requests to `EmailService` -
  both write to `ConversationHistory` like every other turn.
- Fixed a real bug found while testing: `TaskPlanner.prioritize()`'s
  fallback path (GPT unavailable or returned unusable output) computed a
  deterministic plan but never persisted it - `set_priority()` was only
  called on the GPT-sourced path. Also fixed a naive/aware-datetime
  comparison in the fallback's own due-date logic (SQLite drops tzinfo on
  round-trip; every timestamp in this codebase is written as UTC, so a
  naive value read back is safely treated as UTC).
- Verified live against real APIs: created/listed/rescheduled/cancelled
  calendar events; `POST /tasks/prioritize` against real pending tasks
  (GPT correctly ranked an overdue-feeling task "high" with a concrete
  follow-up); `GET /briefing` produced a real, coherent, time-aware
  briefing pulling actual Yahoo Mail unread count and calendar state;
  full document ingest → semantic search → RAG `ask()` round trip,
  including via natural chat ("according to my notes, what is the wifi
  password?") routed through `/think`. 30 new tests (84 total, all
  passing); `ruff check .` clean repo-wide.

## Distributed Voice Pipeline (Mini PC + Raspberry Pi)

- Mini PC: added `GET /voice/connect` (handshake), `WS /voice/stream`
  (chunked audio in, JSON result + WAV audio out, `end_of_turn` framing,
  ping/pong), `POST /voice/transcribe`, `POST /voice/respond`
  (`backend/api/voice.py`). WS endpoint enforces `API_KEY` manually since
  `BaseHTTPMiddleware` doesn't run for websocket scope.
- `VoiceEngine.process_audio()` now also runs speaker verification (gated
  behind `is_enrolled()`) and accepts a `response_format` so Pi-facing
  responses come back as WAV (codec-free playback) while file-based
  callers keep MP3.
- `TextToSpeech.synthesize()` takes a `response_format` parameter; default
  voice changed to `shimmer` (natural female voice per spec).
- New `raspberry_pi/` package (previously empty stub files): `audio/`
  (device discovery/selection by name hint - never a hardcoded index -
  microphone capture, speaker playback with interrupt support, energy VAD,
  diagnostics CLI), `wakeword/` (pluggable `WakeWordEngine`; real
  openWakeWord backend + explicit `NullWakeWordEngine` fallback when no
  trained model is configured), `client/` (`MiniPCClient` REST wrapper,
  `VoiceStreamClient` sync WS client with reconnect-with-backoff,
  `VoiceNode` orchestrator), `health/` (heartbeat monitor for Mini PC/mic/
  speaker availability), plus `config.py`, `logging_config.py`,
  `requirements.txt`, and a systemd unit
  (`systemd/victoria-voice.service`).
- Honest scope limits, not faked: no pretrained "Hello Victoria" wake-word
  model exists (openWakeWord ships generic phrases only - training one
  needs real recorded audio), so the Pi runs in VAD-fallback mode by
  default and the Mini PC's existing text-based wake-word gate (after STT)
  is the real gatekeeper until a model is trained. Speaker verification
  was already gated behind `is_enrolled()` from Sprint 3 and is now fully
  wired into the audio pipeline rather than bypassed.
- Added `docs/VOICE_PIPELINE.md` (protocol, sequence, what's verified vs.
  hardware-dependent) and `docs/DEPLOYMENT.md` (Mini PC + Pi setup steps).
- Verified for real: audio device discovery/selection against this
  machine's actual PortAudio devices (12 inputs, 28 outputs detected);
  `diagnostics.py` recorded real mic input and correctly flagged a
  near-silent level; a full TTS(WAV)->STT->wake-word->GPT-5 round trip
  using real synthesized speech ("Hello Victoria, what is on my calendar
  today?" transcribed back verbatim); the WS `/voice/stream` handshake,
  ping/pong, and end-of-turn round trip against a live server. 26 new
  tests (config, VAD/endpointing, device selection with a fake backend,
  wake-word factory/fallback, Mini PC client with mocked HTTP/WS, health
  monitor) - 80 total, all passing; `ruff check .` clean repo-wide.
- Not verified (documented, not faked): real capture/playback on actual
  Raspberry Pi hardware, a trained wake-word model, real voice biometric
  verification.

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
