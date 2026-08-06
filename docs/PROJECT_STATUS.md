# VictoriaOS v0.2 Runtime — Project Status

Branch: `release/v0.2-runtime` (not merged to `main`).

## v0.2 acceptance goal

> The user says "Hello Victoria," the Pi records the request, audio is sent
> to the Mini PC, Victoria transcribes it, produces a GPT response, speech
> audio returns to the Pi, the Pi plays it, and Victoria remains available
> for a brief follow-up conversation.

**Software status: ready for hardware validation.** Every component in
this flow is implemented, unit/integration tested, and verified as far as
possible without physical Raspberry Pi hardware (see the per-item table
below and `docs/VOICE_PIPELINE.md#status-whats-verified-vs-what-needs-real-hardware`).
Nothing in this flow has been run end-to-end on an actual Pi with a real
microphone and speaker - that is the one remaining step, and it requires
hardware this development environment doesn't have.

## Acceptance criteria, one by one

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Mini PC runs the backend | Ready for hardware validation | `scripts/start_mini_pc.ps1` launches it bound to `0.0.0.0`; boots and serves `/health` in this environment |
| 2 | Pi runs as the voice node | Ready for hardware validation | `raspberry_pi/client/voice_node.py` + systemd unit; logic tested, never run on a physical Pi |
| 3 | User says "Hello Victoria" | Blocked by missing model (wake word) / Ready for hardware validation (VAD-fallback and push-to-talk paths) | No trained wake-word model exists (needs real enrollment audio - see below); VAD-fallback and push-to-talk are fully implemented alternatives that don't need one |
| 4 | Pi records the request | Ready for hardware validation | `Microphone`/VAD/endpointing logic tested with a fake backend; never captured real audio on a Pi |
| 5 | Audio sent to Mini PC | Passed (software) | `WS /voice/stream` chunked-audio + end-of-turn framing verified live over a real WebSocket connection |
| 6 | Victoria transcribes it | Passed (software) | Real OpenAI Whisper round trip verified with real synthesized speech converted to raw PCM and back through the exact wrapping path the Pi uses |
| 7 | Victoria produces a GPT response | Passed (software) | Real GPT-5 calls verified through `VictoriaAssistant.think()`, preserving memory/tasks/Yahoo Mail/conversation context |
| 8 | Speech audio returns to the Pi | Passed (software) | Real OpenAI TTS (WAV) verified; WS binary frame delivery verified live |
| 9 | Pi plays the response | Ready for hardware validation | `Speaker` playback/interruption/overlap-prevention logic tested with a fake backend; never played real audio on a Pi |
| 10 | Brief follow-up conversation | Passed (software) | `ConversationSession` 15s no-wake-word window verified via the text pipeline; same code path for audio |

"Passed (software)" means: verified with real OpenAI API calls and/or real
audio data where a physical device isn't required, and covered by
automated tests that run in CI. It does not mean "run on a Raspberry Pi" -
none of this has been.

## What's genuinely blocking full hardware acceptance

1. **A physical Raspberry Pi with a microphone and speaker.** Everything
   Pi-side has been developed and tested against a fake `sounddevice`
   backend (deterministic, no real audio) plus real-hardware testing of
   the *algorithms* (device discovery, diagnostics, noise calibration) on
   a non-Pi development machine that happens to have real audio hardware.
   The actual Raspberry Pi + ReSpeaker/USB mic + speaker combination has
   never been exercised.
2. **A trained "Hello Victoria" wake-word model.** Not shippable - needs
   real recorded audio of Dr. Opara. VAD-fallback and push-to-talk modes
   are complete, tested workarounds that don't require it (see
   `docs/VOICE_PIPELINE.md`).
3. **Docker image builds.** No Docker daemon is available in this
   development environment. `docker compose config --quiet` confirms the
   compose file itself is syntactically valid; the images have not been
   built or run.

None of the above are "TODO, not started" - they're implemented and tested
to the fullest extent possible without the missing hardware/model/daemon,
with the gap explicitly documented rather than glossed over.

## Test results (this environment)

```
pytest:  103 passed
ruff:    all checks passed (backend, raspberry_pi, tests, scripts)
mypy:    clean on backend/voice, backend/api/voice.py, raspberry_pi
         (pre-existing, unrelated findings in backend/integrations/email/yahoo.py
         left untouched - out of v0.2 runtime scope)
docker compose config --quiet: exit 0 (valid)
```

Run these yourself:

```bash
python -m pytest -q
python -m ruff check backend raspberry_pi tests scripts
python -m mypy backend/voice backend/api/voice.py raspberry_pi --ignore-missing-imports
python -c "import backend.app"          # backend startup smoke test
docker compose config --quiet           # Docker config validation (no daemon needed)
```

## Scope notes

- No login/authentication, weather, Google/Microsoft Calendar, BMW, Home
  Assistant, or other new integrations were added in this release - out of
  scope per the v0.2 runtime freeze. The pre-existing local calendar and
  weather stub (from prior sprints) were left as-is, untouched.
- `frontend/` was not modified.
- Cleanup performed: the duplicate misspelled `backend/api/calender.py`
  stub and `backend/reasoning/excutor.py` (renamed to `executor.py`) were
  already resolved before this release; verified clean (no remaining
  "calender"/"excutor" references anywhere in the repo).
- A real fix landed in this release that the original code had never
  actually exercised: `WS /voice/stream` was calling
  `VoiceEngine.process_audio()` without telling it the audio was raw
  headerless PCM, so it would have gone to Whisper without a valid
  container and either failed or produced garbage. Fixed via
  `backend/voice/audio_format.py` (PCM→WAV wrapping) and an
  `input_format` parameter threading the distinction through
  `process_audio()`. Caught by writing `tests/test_voice_api.py` and
  manually verifying against real OpenAI APIs - not previously tested.
