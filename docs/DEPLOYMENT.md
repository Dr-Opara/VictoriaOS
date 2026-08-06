# Deployment Guide

VictoriaOS runs across two machines on the same LAN:

- **Mini PC** ("Victoria Brain", Windows) — runs the FastAPI backend and
  the dashboard. See [docs/ARCHITECTURE.md](ARCHITECTURE.md) for what's
  inside.
- **Raspberry Pi** ("Voice Node") — runs the microphone/speaker pipeline
  and talks to the Mini PC over the LAN. See
  [docs/VOICE_PIPELINE.md](VOICE_PIPELINE.md) for the protocol.

## Mini PC setup (Windows)

### Option A: one PowerShell command (recommended for LAN/voice-node use)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_mini_pc.ps1
```

This single command:

- loads `.env` and validates required variables are set (`OPENAI_API_KEY`)
  **without ever printing their values** - only "set"/"MISSING"
- warns if `API_KEY` is unset (the API would be unauthenticated on the LAN)
- checks for a Windows Firewall inbound rule on the target port (default
  8000) and offers to create one if running elevated
- prints the Mini PC's LAN IPv4 address(es) - this is what you put in the
  Pi's `MINI_PC_URL`
- starts uvicorn bound to `0.0.0.0` (not just `localhost`), which is
  required for the Pi to reach it

Options: `-Port 8080` to use a different port, `-SkipFirewallCheck` to skip
the firewall step (e.g. if you've already configured it).

### Option B: manual

```powershell
pip install -r requirements.txt
copy .env.example .env   # then edit it - see below
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### Option C: Docker

```bash
cp .env.example .env   # set OPENAI_API_KEY, YAHOO_EMAIL/APP_PASSWORD, API_KEY
docker compose up --build
```

Starts the backend, dashboard, and an nginx reverse proxy (`docker/nginx.conf`).
Validate the compose file itself (no daemon required) with:
`docker compose config --quiet` (exit code 0 = valid; add `--quiet` so it
doesn't print your interpolated secrets to the terminal/logs).
See [README.md](../README.md#deployment) and
[docs/ARCHITECTURE.md](ARCHITECTURE.md#deployment-docker-docker-composeyml-githubworkflowsciyml).

### Required environment variables

Only `OPENAI_API_KEY` is strictly required for the voice pipeline to work
(STT, GPT, TTS all go through it). Recommended for LAN use:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | **Required.** OpenAI API key. |
| `API_KEY` | Shared secret the Pi (and dashboard) must send as `X-API-Key`. Strongly recommended once bound to `0.0.0.0`. |
| `YAHOO_EMAIL` / `YAHOO_APP_PASSWORD` | Optional, for "check my email" to work. |

### Windows Firewall

The backend must accept inbound TCP connections on its port (default 8000)
from the Pi's LAN address. `scripts\start_mini_pc.ps1` checks and offers to
create this automatically when run as Administrator. To do it manually:

```powershell
New-NetFirewallRule -DisplayName "VictoriaOS Backend (8000/TCP)" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

### LAN binding

Binding `0.0.0.0` (not just `127.0.0.1`/`localhost`) is required for the Pi
to reach the backend - `uvicorn backend.app:app --host 0.0.0.0` (both the
PowerShell script and `python -m backend.main` already do this). Find the
Mini PC's LAN IPv4 address with `ipconfig`, or let
`scripts\start_mini_pc.ps1` print it for you. There is no default/hardcoded
LAN IP anywhere in the code - `raspberry_pi/.env.example`'s `MINI_PC_URL`
is a `CHANGE-ME` placeholder you must fill in (or use an mDNS hostname if
you've set one up, e.g. `http://victoria-mini-pc.local:8000`).

### Health endpoint

`GET /health` (no API key required, even when `API_KEY` is set) returns
`{"status": "healthy", "version": "..."}`. Both the Pi's health monitor
(`raspberry_pi/health/monitor.py`) and the dashboard use this to detect
"Mini PC offline."

## Raspberry Pi setup

Assumes Raspberry Pi OS 64-bit, SSH access, and this repository already
cloned (per the project's stated baseline).

```bash
cd ~/VictoriaOS
python3 -m venv .venv-pi
source .venv-pi/bin/activate

# PortAudio is a native dependency of sounddevice:
sudo apt update && sudo apt install -y libportaudio2

pip install -r raspberry_pi/requirements.txt

cp raspberry_pi/.env.example raspberry_pi/.env
```

Edit `raspberry_pi/.env`:

- `MINI_PC_URL` - the Mini PC's LAN address from the step above (e.g.
  `http://192.168.1.42:8000`), **not** the placeholder.
- `API_KEY` - must match the Mini PC's `API_KEY` exactly, if it set one.

### Microphone setup

```bash
python -m raspberry_pi.audio.diagnostics
```

This never falls back to a fake/simulated device - if no real input device
is found, it reports `backend_available: False` or an empty device list
plus a clear warning, not a silently-working fake microphone. It:

- lists every detected input/output device by name
- shows which one `INPUT_DEVICE_HINT`/`OUTPUT_DEVICE_HINT` would select
  (matched by name keyword - never a hardcoded device index, since indices
  shift across reboots/USB re-enumeration)
- records ~1s and reports the peak input level, warning if it's near-silent
  (unplugged/muted mic)

By default `INPUT_DEVICE_HINT=respeaker,seeed,usb` - if you're using a
ReSpeaker array or any USB mic, it should be auto-selected. Otherwise it
falls back to the system default input device, then the first available
one. Set `INPUT_DEVICE_HINT` to a substring of your device's exact name
(shown in the diagnostics output) to force a specific one.

### Speaker setup

Also covered by `python -m raspberry_pi.audio.diagnostics` (output device
list + selection). `OUTPUT_DEVICE_HINT` works the same way as the input
hint; empty means "system default output device."

### Background noise calibration

```bash
python -m raspberry_pi.audio.diagnostics --calibrate-noise
```

Keep the room at its **normal** background noise level (not silent) while
this runs. It records ~2s of ambient noise and recommends a
`VAD_ENERGY_THRESHOLD` value; the diagnostics output warns if your current
setting is too low relative to the measured room noise (a common cause of
false triggers in noisy environments like near a fan or open window).

### Run it directly (for testing)

```bash
python -m raspberry_pi.client.voice_node
```

Watch the log line at startup - it tells you which listening strategy is
active:

- `local wake word` - a trained model is configured and loaded
- `VAD fallback` - no trained model; every detected utterance is streamed
  to the Mini PC, which gates on "Hello Victoria" after transcription
- `push-to-talk (TEST MODE)` - if `PUSH_TO_TALK=true`

### Push-to-talk test mode

If you want to exercise the full pipeline (streaming, STT, GPT, TTS,
playback) on real hardware without a trained wake-word model and without
VAD-fallback's "every sound starts a turn" behavior, set `PUSH_TO_TALK=true`
in `raspberry_pi/.env` and run the voice node **directly in an interactive
terminal** (not via systemd - there's no stdin to read Enter presses under
a service). Press Enter, then speak; the turn ends the normal way (silence
timeout or max utterance length). This is a temporary testing aid, not a
production trigger - see `raspberry_pi/client/push_to_talk.py`.

### Wake word (optional but recommended for production)

Out of the box, the voice node runs in **VAD-fallback mode** - see above.
This works with zero extra setup but sends more audio over the LAN than
necessary and has no wake-word gating on the Pi side (it's still gated by
the Mini PC after transcription, so nothing is acted on without "Hello
Victoria" actually being said - it's a network-efficiency tradeoff, not a
security one).

**Do not treat wake-word detection as "done" without a trained model.**
For low-CPU, always-listening local detection:

1. Record 20-50+ short clips of "Hello Victoria" (varying tone/distance/
   background noise), plus some unrelated speech as negatives.
2. Follow openWakeWord's training notebook/CLI (see the
   [openWakeWord project](https://github.com/dscripka/openWakeWord) for
   the current training process) to produce a `.onnx` model.
3. Copy it to the Pi and set `WAKE_WORD_MODEL_PATH` in
   `raspberry_pi/.env` to its path; set `WAKE_WORD_THRESHOLD` (default
   0.5) to tune sensitivity.
4. Restart the voice node - the startup log should now say
   "listening strategy: local wake word."

Until that model exists, `raspberry_pi/wakeword/factory.py` returns
`NullWakeWordEngine` automatically - the node does not crash and does not
fake a detection.

### Install as a systemd service (for production)

```bash
# Install
sudo cp raspberry_pi/systemd/victoria-voice.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable victoria-voice.service   # start automatically on boot,
                                                # after network-online.target

# Start / stop / restart
sudo systemctl start victoria-voice.service
sudo systemctl stop victoria-voice.service
sudo systemctl restart victoria-voice.service

# Status
sudo systemctl status victoria-voice.service

# Logs (journal, since the unit sets StandardOutput/Error=journal)
journalctl -u victoria-voice.service -f        # follow live
journalctl -u victoria-voice.service -n 200    # last 200 lines
```

The unit also writes its own structured, rotated log file independent of
the journal: `raspberry_pi/logs/voice_node.log` (see
`raspberry_pi/logging_config.py`).

Restart behavior: `Restart=on-failure` with a 5s delay - if the process
crashes (uncaught exception, not a handled reconnect), systemd restarts it.
Recoverable errors (mic/speaker disconnect, Mini PC unreachable) are
handled *inside* the process with backoff/retry and do not crash it - see
`raspberry_pi/client/voice_node.py`.

Edit the unit file first if your username/paths differ from `pi`/
`/home/pi/VictoriaOS` (see `raspberry_pi/systemd/victoria-voice.service`).
**`PUSH_TO_TALK` must stay `false`/unset under systemd** - there's no
interactive terminal for it to read from.

## Verifying the end-to-end pipeline

1. On the Mini PC: `curl http://localhost:8000/health` -> `{"status":"healthy",...}`
2. On the Pi: `python -m raspberry_pi.audio.diagnostics` -> no warnings
3. On the Pi:
   ```bash
   python -c "from raspberry_pi.client.connection import MiniPCClient; from raspberry_pi.config import get_config; print(MiniPCClient(get_config()).connect())"
   ```
   -> should print a `ConnectInfo` with a fresh `session_id` (confirms LAN
   connectivity + API key match)
4. Start the voice node (`python -m raspberry_pi.client.voice_node`, or via
   systemd) and speak the wake phrase (or, in VAD-fallback/push-to-talk
   mode, just speak/press Enter) - check `raspberry_pi/logs/voice_node.log`
   on the Pi and `logs/victoria.log` on the Mini PC for the turn round
   trip and latency.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Pi logs "Mini PC unavailable; retrying" forever | Wrong `MINI_PC_URL`, backend not bound to `0.0.0.0`, or firewall blocking the port | Verify `curl http://<mini-pc-ip>:8000/health` from the Pi itself; re-check firewall rule and `--host 0.0.0.0` |
| Pi connects but every request gets `401` | `API_KEY` mismatch between Mini PC and Pi | Make sure both `.env` files have the exact same `API_KEY` |
| `raspberry_pi.audio.devices.AudioBackendUnavailable: PortAudio is not available` | `libportaudio2` not installed | `sudo apt install libportaudio2` |
| `AudioBackendUnavailable: No audio input devices were found` | Mic not plugged in, or wrong USB port/hub | Check `lsusb`, replug, re-run diagnostics |
| Diagnostics reports near-silent input level | Mic muted, gain too low, or wrong device selected | Check `alsamixer`, confirm `INPUT_DEVICE_HINT` matches the intended device's name |
| Wake word never triggers | No trained model (`WAKE_WORD_MODEL_PATH` unset) - **this is not a bug**, it's VAD-fallback mode | Confirm the startup log says "VAD fallback"; either accept that mode or train a model (see above) |
| Every utterance is sent even when nobody's talking | `VAD_ENERGY_THRESHOLD` too low for the room's ambient noise | `python -m raspberry_pi.audio.diagnostics --calibrate-noise` and raise the threshold to the recommendation |
| Recording never stops / runs to `MAX_UTTERANCE_SECONDS` every time | `SILENCE_TIMEOUT_MS` too long, or background noise never drops below threshold | Lower `SILENCE_TIMEOUT_MS`, or raise `VAD_ENERGY_THRESHOLD` per the calibration above |
| Playback is silent but no error | Wrong output device selected, or system volume/mute | Check `OUTPUT_DEVICE_HINT`, system volume, `aplay -l` |
| `MicrophoneDisconnectedError` / `SpeakerDisconnectedError` in the log | Device physically unplugged or a driver crash | The voice node logs this clearly and retries device selection every few seconds rather than hanging or crashing - replug the device |
| Push-to-talk does nothing | Running under systemd (no interactive stdin), or `PUSH_TO_TALK=false` | Run `python -m raspberry_pi.client.voice_node` directly in a terminal with `PUSH_TO_TALK=true` |
| `docker compose config` prints your API keys | This is expected - `config` interpolates `.env` for display | Use `docker compose config --quiet` (exit-code only) when you just need to validate syntax, and avoid pasting the full `config` output anywhere |
