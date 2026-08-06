# VictoriaOS

Victoria is an intelligent executive AI assistant built by Dr. Opara.

Victoria is voice-first, privacy-first, and security-first.

Unlike traditional assistants, Victoria reasons, plans, remembers, and proactively assists while keeping the user in control.

Version: 1.0

## Capabilities

- **Persistent memory** — remembers facts, preferences, and conversation history across restarts (SQLite via SQLAlchemy).
- **Executive assistant** — tracks tasks, recalls preferences ("remember my favorite airline is United"), and answers "what do you remember about me?".
- **Context-aware GPT** — every request flows through the AI Context Builder, so replies are grounded in prior conversation, preferences, and open tasks.
- **Yahoo Mail** — reads and summarizes unread mail.
- **Voice pipeline** — wake word ("Hello Victoria"), voice activity detection, speech-to-text/text-to-speech, speaker gating, and multi-turn conversation mode. Runs across two machines: a Mini PC brain and a Raspberry Pi voice node — see [docs/VOICE_PIPELINE.md](docs/VOICE_PIPELINE.md).
- **Executive Daily Briefing** — a spoken-style GPT-5 summary of today's calendar, weather, unread email, and tasks, with a personalized greeting (`GET /briefing`, `GET /briefing/voice`).
- **Calendar** — a real local calendar (create/reschedule/cancel/today/upcoming); Google/Microsoft sync is a documented stub pending OAuth credentials.
- **Knowledge Engine (RAG)** — upload documents (PDF/Word/PowerPoint/Excel/text/OCR'd images), semantic search, and GPT-5 Q&A with cited sources — reachable from chat too ("according to my notes...").
- **Intelligent task prioritization** — GPT ranks pending tasks by urgency/importance with a one-line follow-up each, falling back to a deterministic due-date heuristic if GPT is unavailable.
- **Executive Dashboard** — Next.js/React web UI (Chat, Voice, Email, Memory, Tasks, Calendar, Weather, AI Usage, Logs, Settings) backed by the same API.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/VOICE_PIPELINE.md](docs/VOICE_PIPELINE.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), [docs/ROADMAP.md](docs/ROADMAP.md), and [docs/CHANGELOG.md](docs/CHANGELOG.md).

## Running locally

Backend:

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in OPENAI_API_KEY, YAHOO_EMAIL, YAHOO_APP_PASSWORD
uvicorn backend.app:app --reload
```

The SQLite database is created automatically on startup at `data/victoria.db`.

Dashboard:

```bash
cd frontend/dashboard
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL, defaults to http://localhost:8000
npm run dev
```

## Testing

```bash
python -m pytest
python -m ruff check backend   # if ruff is installed

cd frontend/dashboard
npm run lint
npm run build
```

## Deployment

```bash
cp .env.example .env   # set API_KEY before exposing this beyond localhost
docker compose up --build
```

Runs the backend, dashboard, and an nginx reverse proxy (`docker/nginx.conf`,
routes `/api/*` to the backend, everything else to the dashboard). See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for what each container does.
CI (`.github/workflows/ci.yml`) lints and tests both the backend and
dashboard on every push/PR to `main`.

## Security

- Set `API_KEY` to require an `X-API-Key` header on every request except
  `/health` and the docs — unset, the API is unauthenticated (fine for
  local dev, not for anything beyond localhost).
- `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` control the built-in
  rate limiter (default 120 requests / 60s per IP).
- Memory and task mutations are written to `logs/audit.log` separately from
  the general request log.

## Key endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/think?command=...&session_id=...` | Send a command to Victoria |
| GET | `/memory?query=...` | List/search remembered facts |
| POST | `/remember` | Store a fact (`{"key": "...", "value": "..."}`) |
| POST | `/forget` | Delete a remembered fact (`{"key": "..."}`) |
| GET | `/tasks?status=...` | List tasks |
| POST | `/tasks` | Create a task |
| POST | `/tasks/{id}/complete` | Complete a task |
| DELETE | `/tasks/{id}` | Delete a task |
| POST | `/voice/command` | Full voice pipeline (audio file in, audio out) |
| GET | `/voice/connect` | Voice-node handshake: session id + stream params |
| WS | `/voice/stream` | Duplex streaming: chunked audio in, JSON result + WAV out |
| POST | `/voice/transcribe` | Audio in, transcript only |
| POST | `/voice/respond` | Text in, spoken reply out (no wake-word gate) |
| GET | `/email/unread` | Unread Yahoo Mail messages |
| GET | `/system/status` | Uptime, version, environment, model |
| GET | `/system/usage` | Conversation/memory/task counts |
| GET | `/system/logs?limit=...` | Tail of the application log |
| GET | `/briefing` / `/briefing/voice` | Executive daily briefing (text / spoken audio) |
| GET | `/calendar/today`, `/calendar/upcoming` | Calendar views |
| POST/PATCH/DELETE | `/calendar/events[/{id}]` | Create/reschedule/cancel events |
| GET | `/weather/current` | Current conditions (`{"configured": false}` if unset) |
| POST | `/tasks/prioritize` | GPT-driven task prioritization |
| POST/GET/DELETE | `/knowledge/documents[/{id}]` | Ingest / list / delete documents |
| GET | `/knowledge/search?q=...` | Semantic search over documents |
| POST | `/knowledge/ask` | RAG question answering with cited sources |
