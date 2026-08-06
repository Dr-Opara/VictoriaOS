# Frontend Changelog

## v0.2 Dashboard Release

- Rebuilt the Home dashboard around release-scope backend APIs only, removing the previous weather and calendar widgets.
- Connected the Victoria AI Core to real dashboard states: idle, listening, thinking, speaking, offline, and error.
- Completed Assistant chat with backend `/think` calls, local conversation history, progressive response reveal, markdown/code rendering, copy actions, browser voice-state visualization, and clear loading/error handling.
- Completed Memory, Knowledge, Yahoo Mail, Tasks, and Settings pages with backend-backed actions, empty/loading/error states, toast notifications, keyboard-accessible controls, and responsive desktop/tablet layouts.
- Added honest unavailable states for backend gaps: memory pinning, full Yahoo message bodies, Yahoo draft replies, direct task patching, and task due-date writes.
- Added shared markdown rendering, local chat persistence, skeleton loaders, upload progress, and v0.2 package metadata.

## Validation

- `npm install`
- `npm run lint`
- `npm run build`
- No frontend test script or frontend test files exist in `frontend/dashboard` for v0.2.
