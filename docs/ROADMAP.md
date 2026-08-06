# VictoriaOS Roadmap

## Executive Dashboard

- [x] Next.js 16 / React 19 / TypeScript / Tailwind CSS 4 web app (`frontend/dashboard`)
- [x] Dark mode by default, sidebar + mobile nav, TanStack Query polling for near-real-time data
- [x] Chat, Voice (browser STT demo), Email, Memory, Tasks, AI Usage, Logs, Settings
- [ ] Calendar / Weather pages are wired up but show a "not connected" state — they need a
      calendar OAuth provider and a weather API key respectively before going live
- [ ] True real-time updates (WebSocket/SSE) — currently polling every 5-30s per section
- [ ] Authenticated dashboard access (currently assumes a trusted local network)

## Core Platform

- [x] Configuration
- [x] Logging
- [x] Database (SQLite via SQLAlchemy)
- [x] Memory (persistent, survives restarts)
- [x] Brain / Orchestrator
- [x] Skills
- [x] Security: shared API key auth, rate limiting, security headers, audit log
- [ ] Multi-user roles/RBAC — not applicable yet; VictoriaOS is single-user (Dr. Opara) by design
- [ ] Encrypted secrets at rest (currently plain `.env`; fine for a single local deployment,
      revisit if secrets move to a shared/cloud host)

## Production / Deployment

- [x] `docker/backend.Dockerfile`, `docker/frontend.Dockerfile` (Next.js standalone output)
- [x] `docker-compose.yml` (backend + frontend + nginx reverse proxy)
- [x] `docker/nginx.conf` reverse proxy (HTTP; TLS termination point is there but no
      certificate is generated — needs a real domain)
- [x] GitHub Actions CI (`.github/workflows/ci.yml`): backend lint+test, frontend lint+build,
      on every push/PR to main
- [x] Docker healthcheck (`/health`) on the backend container
- [x] `scripts/backup_db.py` — SQLite online backup + retention pruning
- [ ] Docker images are unbuilt/unverified in this environment (no Docker daemon available
      here) — build and smoke-test `docker compose up` before relying on them in production
- [ ] Automated recurring backups (the script exists; nothing schedules it yet — cron/Task
      Scheduler/systemd timer needed on the host)

## Voice

- [x] Wake word ("Hello Victoria") — text-gate on the Mini PC (`backend/voice/wakeword.py`);
      framework + graceful fallback for local Pi-side detection (`raspberry_pi/wakeword/`)
- [x] Voice activity detection / silence detection / interruption handling (both sides)
- [x] Speech-to-text (OpenAI), Text-to-speech (OpenAI, WAV for codec-free Pi playback)
- [x] Conversation mode (multi-turn without repeating the wake word)
- [x] Mini PC <-> Raspberry Pi distributed pipeline: `/voice/connect`, `/voice/stream`
      (WebSocket, chunked audio + end-of-turn framing), `/voice/transcribe`, `/voice/respond`
- [x] Pi-side reconnect-with-backoff (HTTP handshake + WebSocket) and health heartbeat
- [x] Speaker verification interface fully wired into the pipeline, gated behind
      `is_enrolled()` (see Core Platform below for what's missing)
- [ ] A trained "Hello Victoria" openWakeWord model — needs real recorded enrollment audio;
      until then the Pi runs in VAD-fallback mode (see `docs/VOICE_PIPELINE.md`)
- [ ] Real speaker (voice biometric) verification — needs an enrolled voiceprint + embedding
      model + real enrollment audio from Dr. Opara
- [ ] Actual ReSpeaker/USB mic capture verified on Raspberry Pi hardware — device discovery,
      diagnostics, VAD, and reconnect logic are all real and tested against real audio
      hardware on the Mini PC's own machine, but not yet run on a physical Pi
- [ ] Multi-microphone array beamforming / noise suppression tuning

## Intelligence

- [x] OpenAI integration
- [x] AI Context Builder (history + preferences + tasks -> every GPT call)
- [ ] Reasoning / planning beyond single-turn GPT calls
- [ ] Proactive memory retrieval (semantic search / embeddings)

## Productivity

- [x] Yahoo Mail
- [x] Tasks (create/complete/delete/list + due-task polling)
- [ ] Gmail
- [ ] Calendar
- [ ] Contacts
- [ ] Notes
- [ ] Reminders (scheduled delivery, not just polling)

## Communications

- [ ] Calls
- [ ] SMS
- [ ] WhatsApp (future)

## Travel

- [ ] Flights
- [ ] Hotels
- [ ] Rental cars

## Vehicle

- [ ] BMW

## Home

- [ ] Home Assistant
- [ ] Thermostat
- [ ] Cameras
- [ ] Lights
- [ ] Locks

## Future

- [ ] Vision
- [ ] Mobile app
- [ ] Apple Watch
- [ ] Android
- [ ] Multi-room
