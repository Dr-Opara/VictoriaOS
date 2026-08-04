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
- **Voice pipeline** — wake word ("Hello Victoria"), voice activity detection, speech-to-text/text-to-speech, speaker gating, and multi-turn conversation mode.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/ROADMAP.md](docs/ROADMAP.md), and [docs/CHANGELOG.md](docs/CHANGELOG.md).

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in OPENAI_API_KEY, YAHOO_EMAIL, YAHOO_APP_PASSWORD
uvicorn backend.app:app --reload
```

The SQLite database is created automatically on startup at `data/victoria.db`.

## Testing

```bash
python -m pytest
python -m ruff check backend   # if ruff is installed
```

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
| POST | `/voice/command` | Full voice pipeline (audio in, audio out) |
