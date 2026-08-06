# VictoriaOS Voice Pipeline

Two machines, one conversation:

```
Mini PC (Windows, "Victoria Brain")        Raspberry Pi ("Voice Node")
------------------------------------       ---------------------------
FastAPI backend                            Microphone (ReSpeaker/USB)
  /voice/connect                              |
  /voice/stream   <===== LAN WebSocket =====>  Wake word (local, optional)
  /voice/transcribe                            VAD end-pointing
  /voice/respond                               |
GPT-5 (via Context Builder)                 Pi Client (reconnect+backoff)
Memory / Tasks / Yahoo Mail                    |
OpenAI STT + TTS                             Speaker playback
```

**The Pi never calls OpenAI or GPT directly.** Every capability the voice
node has is a thin wrapper around the Mini PC's `/voice/*` API
(`raspberry_pi/client/connection.py`). This keeps API keys off the edge
device and keeps "what Victoria knows" (memory, preferences, tasks,
conversation history) in exactly one place.

## Turn-by-turn flow

1. **Wake / trigger.** One of three strategies decides this (see below):
   the Pi's local wake-word engine fires, the user presses Enter
   (push-to-talk test mode), or - in VAD-fallback mode - the VAD detects
   speech and starts a turn unconditionally.
2. **Capture.** The Pi streams raw PCM chunks to `WS /voice/stream` as
   they're captured, and its own `EndpointDetector`
   (`raspberry_pi/audio/vad.py`) watches for sustained silence.
   `MAX_UTTERANCE_SECONDS` hard-caps how long a single turn can run even if
   silence is never detected (e.g. continuous background noise), so a
   stuck open mic can't record forever.
3. **End of turn.** The Pi sends `{"event": "end_of_turn"}`. The Mini PC
   assembles the buffered audio and runs `VoiceEngine.process_audio()`
   (`backend/voice/engine.py`): VAD sanity check → optional speaker
   verification → the PCM is wrapped into a real WAV container
   (`backend/voice/audio_format.py` - STT providers need an actual audio
   file, not headerless samples) → OpenAI STT → wake-word-in-text gate /
   conversation-mode check → `VictoriaAssistant.think()` (Context Builder →
   GPT-5) → OpenAI TTS (WAV, for codec-free playback on the Pi).
4. **Reply.** The Mini PC sends a `result` JSON frame (status, transcript,
   message, latency) followed by a binary WAV frame. The Pi plays it
   non-blocking so it can keep listening for an interruption: if the VAD
   detects speech while Victoria is talking, playback stops immediately
   (`Speaker.stop()` in `raspberry_pi/audio/speaker.py`) and the buffered
   mic audio since is discarded (`Microphone.drain()`) before the next
   turn starts, so stale audio captured during playback never leaks into
   the next transcription.
5. **Conversation mode.** For 15 seconds after a reply, the *Mini PC* stays
   "awake" for that session (`ConversationSession` in
   `backend/voice/engine.py`) and skips the wake-word gate — so a
   VAD-triggered turn is enough to keep talking, matching Phase 9's "no
   wake word for 15 seconds" requirement without needing the Pi and the
   Mini PC to independently track the same timer.

## Three listening strategies

VictoriaOS picks automatically (`raspberry_pi/client/voice_node.py`):

| | Local wake word | Push-to-talk | VAD fallback |
|---|---|---|---|
| Trigger | openWakeWord scores each frame locally | Enter keypress (interactive terminal only) | Any detected speech starts a turn |
| CPU | Low — the always-on cost is just a small ONNX model | Low | Low — energy threshold only |
| Network use | Only after "Hello Victoria" | Only after Enter | Every utterance, gated server-side after STT |
| Requires | A **trained** wake-word model (see below) | `PUSH_TO_TALK=true`, run directly (not systemd) | Nothing extra |
| Use case | Production | Hardware testing without a trained model | Zero-setup fallback |

Push-to-talk (`raspberry_pi/client/push_to_talk.py`) is explicitly a
**temporary testing aid**: it exists so the rest of the pipeline can be
exercised on real hardware without either a trained wake-word model or
VAD-fallback's higher false-trigger rate. It requires an interactive stdin
and logs a clear warning (rather than silently doing nothing) if run under
systemd, where there's no terminal to read from.

**There is no pretrained "Hello Victoria" model.** openWakeWord
(https://github.com/dscripka/openWakeWord) is a real, non-mock streaming
wake-word framework, but its bundled models are generic phrases ("hey
jarvis", "alexa"). Training a custom model needs real recorded audio of Dr.
Opara saying "Hello Victoria" (and ideally some negative/background audio),
run through openWakeWord's training pipeline. That's a manual, one-time
step this repo cannot do for you:

1. Record 20-50+ short clips of "Hello Victoria" (varying tone/distance/
   background noise), plus some clips of unrelated speech as negatives.
2. Follow openWakeWord's training notebook/CLI
   (see the project's `docs/` and `notebooks/` for the current process) to
   produce an `.onnx` model.
3. Copy it to the Pi and set `WAKE_WORD_MODEL_PATH` in
   `raspberry_pi/.env` to its path.

Until that file exists, `raspberry_pi/wakeword/factory.py` returns
`NullWakeWordEngine` and the voice node **automatically and silently**
(from the user's perspective) runs in VAD-fallback mode — it does not crash
and it does not fake a detection.

## Speaker verification

Same principle, server-side this time (`backend/voice/speaker.py`,
`SpeakerAuthenticator`): `verify_audio()` is fully wired into
`VoiceEngine.process_audio()`, gated behind `is_enrolled()`. With no
enrolled voiceprint, verification is skipped entirely (single-trusted-user
assumption) rather than faked. Enrolling a real voiceprint needs a chosen
embedding model and real enrollment audio - tracked in the roadmap, not
implemented blind.

## Health monitoring, reconnection, and disconnects

- `raspberry_pi/health/monitor.py` polls the Mini PC's `/health` and the
  local mic/speaker device lists every `HEARTBEAT_INTERVAL_SECONDS`
  (default 10s) and logs state transitions (e.g.
  `mini_pc: ok -> unavailable`) - this is the "clear offline state": you
  will see exactly when and what went offline in the log, not silence.
- `raspberry_pi/client/connection.py` reconnects both the initial HTTP
  handshake and the WebSocket stream with exponential backoff
  (`RECONNECT_INITIAL_DELAY_SECONDS` → `RECONNECT_MAX_DELAY_SECONDS`,
  capped). Request-level timeouts (`REQUEST_TIMEOUT_SECONDS`, default 30s)
  bound how long the Pi waits for a single turn's result before the
  session is treated as broken and reconnected.
- **Device disconnects**: `Microphone`/`Speaker` (`raspberry_pi/audio/`)
  never hang silently or fall back to a fake device if the real one drops
  mid-stream. `MicrophoneDisconnectedError`/`SpeakerDisconnectedError` are
  raised as soon as PortAudio reports the stream is no longer active; the
  voice node's main loop catches these specifically, logs a clear
  "microphone/speaker disconnected" message, and retries device selection
  after a short backoff rather than crashing the process.
- "Pi offline" and "OpenAI unavailable" are, by construction, visible from
  the *other* side: the Mini PC stops receiving heartbeats from a dead Pi,
  and `GET /system/status` already reports the configured model/environment
  for the Mini PC itself.

## Configuration

All Pi-side configuration is environment variables, documented in
`raspberry_pi/.env.example`. Notably: `MINI_PC_URL` (no default LAN IP -
you must set it), `API_KEY` (must match the Mini PC's `API_KEY` if it's
set), `INPUT_DEVICE_HINT` / `OUTPUT_DEVICE_HINT` (comma-separated name
keywords, never a hardcoded device index), `WAKE_WORD_MODEL_PATH`,
`PUSH_TO_TALK`, `REQUEST_TIMEOUT_SECONDS`, and the VAD/timeout tuning
knobs.

## Status: what's verified vs. what needs real hardware

**Passed on hardware:** none of this has been run on an actual Raspberry
Pi with a physical microphone/speaker yet - see below for what that
requires. See also `docs/PROJECT_STATUS.md` for the full v0.2 status.

**Ready for hardware validation** (implemented and verified as far as
possible without the physical device; needs a real Pi + mic + speaker to
confirm end-to-end):

- Audio device discovery/selection/diagnostics/noise-calibration - logic
  verified against real PortAudio devices on a development machine (not a
  Pi), including a real recorded near-silent-level warning
- TTS → STT round trip through the real OpenAI APIs, including the PCM →
  WAV wrapping fix that makes streamed Pi audio actually transcribable
  (verified with real synthesized speech converted to raw PCM and back)
- The full text pipeline (wake word → GPT-5 → context-aware reply) via
  `VoiceEngine.process()`
- The Mini PC's `/voice/connect`, `/voice/stream` (WS handshake, ping/pong,
  end-of-turn round trip, PCM-to-WAV path), `/voice/transcribe`,
  `/voice/respond`, `/voice/command` - all covered by automated tests
  (`tests/test_voice_api.py`) with mocked STT/GPT/TTS calls
- Reconnect-with-backoff, device-disconnect handling, VAD/endpointing,
  wake-word fallback/push-to-talk selection logic (unit tested with real
  algorithms, fake I/O boundaries - `tests/raspberry_pi/`)
- systemd unit file syntax and restart/logging configuration (not run
  under an actual systemd instance)

**Blocked by missing device or model** (cannot be validated at all without
it, not attempted, not claimed as working):

- Actual ReSpeaker/USB mic capture and playback on Raspberry Pi hardware
- A trained "Hello Victoria" wake-word model (needs real enrollment audio)
- Real speaker (voice biometric) verification (needs an enrolled
  voiceprint + embedding model)
- Multi-microphone array beamforming/noise suppression tuning
- Docker image builds (no Docker daemon in this development environment;
  `docker compose config --quiet` validates the compose file's syntax only)
