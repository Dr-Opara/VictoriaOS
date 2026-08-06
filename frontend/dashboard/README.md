# VictoriaOS Dashboard

Next.js 16 dashboard for the VictoriaOS v0.2 release. The dashboard talks only to the existing VictoriaOS backend APIs and does not add authentication, calendar, weather, BMW, Home Assistant, mobile, or new integration flows.

## Requirements

- Node.js 20+
- VictoriaOS backend running at `http://localhost:8000` unless `NEXT_PUBLIC_API_URL` is set
- Optional `NEXT_PUBLIC_API_KEY` when the backend is protected by `API_KEY`

## Commands

```bash
npm install
npm run lint
npm run build
npm run dev
```

Open `http://localhost:3000` for local development.

## Environment

Create `frontend/dashboard/.env.local` when local defaults are not enough:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=
```

Only `NEXT_PUBLIC_*` values are sent to the browser.

## v0.2 Surface

- Home dashboard with Victoria AI Core, executive briefing, Yahoo Mail summary, task summary, memory summary, recent local conversation, Mini PC/API health, Raspberry Pi voice handshake status, OpenAI/model status, database usage health, and knowledge-store health.
- Assistant page with working backend chat, local conversation history, progressive response reveal, markdown/code rendering, copy response, browser speech input state, loading state, and API error handling.
- Memory page with list, search, create, key-level replace, delete, loading/empty/error states, and disabled pin controls where the backend has no pin support.
- Knowledge page with document upload, upload progress, document list, semantic search, source-cited Q&A, delete, loading/empty/error states.
- Yahoo Mail page with unread inbox view, priority signals from loaded unread messages, AI summary through `/think`, message preview reading, search over loaded unread messages, and disabled full-body/draft controls where the backend has no API.
- Tasks page with create, complete, delete, AI prioritization, replacement-based edit, due-date/status/priority display, and list/board views.
- Settings page limited to v0.2: OpenAI/backend model status, Yahoo Mail status, voice configuration, Raspberry Pi voice handshake, microphone/speaker browser status, appearance, memory controls, and about/version.

## Backend APIs Used

- `/health`
- `/system/status`
- `/system/usage`
- `/briefing`
- `/think`
- `/email/unread`
- `/memory`, `/remember`, `/forget`
- `/tasks`, `/tasks/{id}/complete`, `/tasks/{id}`, `/tasks/prioritize`
- `/knowledge/documents`, `/knowledge/search`, `/knowledge/ask`
- `/voice/connect`

Calendar and weather widgets are intentionally absent from the v0.2 dashboard surface. The frontend also does not expose login/authentication configuration.

## Validation

For the v0.2 dashboard release, run:

```bash
npm install
npm run lint
npm run build
```

There is no frontend test script or frontend test file in this package as of v0.2. Add a `test` script here before treating frontend tests as a CI gate.
