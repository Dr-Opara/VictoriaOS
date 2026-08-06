# Frontend Project Status

## VictoriaOS v0.2 Dashboard

Status: validated on branch `release/v0.2-dashboard`.

Completed dashboard scope:

- Home dashboard
- AI Core states
- Assistant page
- Memory page
- Knowledge page
- Yahoo Mail page
- Tasks page
- Settings page
- Shared skeleton, empty, error, toast, focus, and reduced-motion handling

Intentional v0.2 exclusions:

- Login and authentication UI
- Weather widgets or configuration
- Calendar widgets or configuration
- BMW, Home Assistant, mobile app, or new integrations

Known backend capability limits surfaced honestly in the UI:

- Memory pinning is unavailable.
- Yahoo Mail full-body reading and draft replies are unavailable.
- Task patching and due-date writes are unavailable; task edits use a replacement flow.
- Raspberry Pi status is limited to the backend voice handshake because no Pi heartbeat endpoint is exposed.

Validation checklist:

- `npm install`: passing
- `npm run lint`: passing
- `npm run build`: passing
- `npm run test --if-present`: passing; no frontend test script is currently defined
