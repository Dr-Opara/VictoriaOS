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

1. **Wake / trigger.** Either the Pi's local wake-word engine fires, or (in
   VAD-fallback mode — see below) the VAD detects speech and starts a turn
   unconditionally.
2. **Capture.** The Pi streams raw PCM chunks to `WS /voice/stream` as
   they're captured, and its own `EndpointDetector`
   (`raspberry_pi/audio/vad.py`) watches for sustained silence.
3. **End of turn.** The Pi sends `{"event": "end_of_turn"}`. The Mini PC
   assembles the buffered audio and runs `VoiceEngine.process_audio()`
   (`backend/voice/engine.py`): VAD sanity check → optional speaker
   verification → OpenAI STT → wake-word-in-text gate / conversation-mode
   check → `VictoriaAssistant.think()` (Context Builder → GPT-5) → OpenAI
   TTS (WAV, for codec-free playback on the Pi).
4. **Reply.** The Mini PC sends a `result` JSON frame (status, transcript,
   message, latency) followed by a binary WAV frame. The Pi plays it and
   goes back to listening.
5. **Conversation mode.** For 15 seconds after a reply, the *Mini PC* stays
   "awake" for that session (`ConversationSession` in
   `backend/voice/engine.py`) and skips the wake-word gate — so a
   VAD-triggered turn is enough to keep talking, matching Phase 9's "no
   wake word for 15 seconds" requirement without needing the Pi and the
   Mini PC to independently track the same timer.

## Two listening strategies

VictoriaOS ships both, and picks automatically
(`raspberry_pi/client/voice_node.py`):

| | Local wake word | VAD fallback |
|---|---|---|
| Trigger | openWakeWord scores each frame locally | Any detected speech starts a turn |
| CPU | Low — the always-on cost is just a small ONNX model | Low — energy threshold only |
| Network use | Only after "Hello Victoria" | Every utterance, gated server-side after STT |
| Requires | A **trained** wake-word model (see below) | Nothing extra |

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

## Health monitoring & reconnection

- `raspberry_pi/health/monitor.py` polls the Mini PC's `/health` and the
  local mic/speaker device lists every `HEARTBEAT_INTERVAL_SECONDS`
  (default 10s) and logs state transitions.
- `raspberry_pi/client/connection.py` reconnects both the initial HTTP
  handshake and the WebSocket stream with exponential backoff
  (`RECONNECT_INITIAL_DELAY_SECONDS` → `RECONNECT_MAX_DELAY_SECONDS`).
- "Pi offline" and "OpenAI unavailable" are, by construction, visible from
  the *other* side: the Mini PC stops receiving heartbeats from a dead Pi,
  and `GET /system/status` already reports the configured model/environment
  for the Mini PC itself.

## Configuration

All Pi-side configuration is environment variables, documented in
`raspberry_pi/.env.example`. Notably: `MINI_PC_URL`, `API_KEY` (must match
the Mini PC's `API_KEY` if it's set), `INPUT_DEVICE_HINT` /
`OUTPUT_DEVICE_HINT` (comma-separated name keywords, never a hardcoded
device index), `WAKE_WORD_MODEL_PATH`, and the VAD/timeout tuning knobs.

## What's verified vs. what needs real hardware

Verified in this repo (real audio, real API calls, no mocks):

- Audio device discovery/selection against real PortAudio devices
- TTS → STT round trip through the real OpenAI APIs (WAV format)
- The full text pipeline (wake word → GPT-5 → context-aware reply) via
  `VoiceEngine.process()`
- The Mini PC's `/voice/connect`, `/voice/stream` (WS handshake, ping/pong,
  end-of-turn round trip), `/voice/transcribe`, `/voice/respond`
- Reconnect-with-backoff logic, device selection logic, VAD/endpointing
  logic, wake-word fallback logic (all unit tested with real algorithms,
  fake I/O boundaries)

Cannot be verified without the physical setup (documented, not faked):

- Actual ReSpeaker/USB mic capture and playback on Raspberry Pi hardware
- A trained "Hello Victoria" wake-word model
- Real speaker (voice biometric) verification
- Multi-microphone array beamforming/noise suppression tuning
