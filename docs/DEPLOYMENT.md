# Deployment Guide

VictoriaOS runs across two machines on the same LAN:

- **Mini PC** ("Victoria Brain") — runs the FastAPI backend and the
  dashboard. See [docs/ARCHITECTURE.md](ARCHITECTURE.md) for what's inside.
- **Raspberry Pi** ("Voice Node") — runs the microphone/speaker pipeline
  and talks to the Mini PC over the LAN. See
  [docs/VOICE_PIPELINE.md](VOICE_PIPELINE.md) for the protocol.

## Mini PC setup

### Option A: Docker (recommended for anything beyond local dev)

```bash
cp .env.example .env   # set OPENAI_API_KEY, YAHOO_EMAIL/APP_PASSWORD, API_KEY
docker compose up --build
```

Starts the backend, dashboard, and an nginx reverse proxy (`docker/nginx.conf`).
See [README.md](../README.md#deployment) and
[docs/ARCHITECTURE.md](ARCHITECTURE.md#deployment-docker-docker-composeyml-githubworkflowsciyml).

### Option B: Directly with Python

```bash
pip install -r requirements.txt
cp .env.example .env
python -m backend.main   # or: uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Binding `0.0.0.0` (not just `localhost`) is required for the Pi to reach it
over the LAN. **Set `API_KEY` before doing this** — without it, anything on
the LAN can call the API (see [README.md#security](../README.md#security)).

Find the Mini PC's LAN IP (`ipconfig` on Windows) — the Pi's
`MINI_PC_URL` points at `http://<that-ip>:8000`.

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
# Edit raspberry_pi/.env: set MINI_PC_URL to the Mini PC's LAN IP,
# and API_KEY to match the Mini PC's, if set.
```

### Verify the audio hardware first

```bash
python -m raspberry_pi.audio.diagnostics
```

This lists every detected input/output device, the one that would be
auto-selected (by `INPUT_DEVICE_HINT`/`OUTPUT_DEVICE_HINT`, never a
hardcoded index), and a live input level reading. Fix any warnings it
prints (unplugged mic, near-silent level, muted device) before continuing.

### Run it directly (for testing)

```bash
python -m raspberry_pi.client.voice_node
```

### Install as a systemd service (for production)

```bash
sudo cp raspberry_pi/systemd/victoria-voice.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now victoria-voice.service
sudo systemctl status victoria-voice.service
journalctl -u victoria-voice.service -f
```

Edit the unit file first if your username/paths differ from `pi`/
`/home/pi/VictoriaOS` (see `raspberry_pi/systemd/victoria-voice.service`).

### Wake word (optional but recommended)

Out of the box, the voice node runs in **VAD-fallback mode**: it starts
streaming on any detected speech and lets the Mini PC's text-based
wake-word gate decide whether "Hello Victoria" was said. This works with
zero extra setup but sends more audio over the LAN than necessary.

For low-CPU, always-listening local wake-word detection, train a custom
openWakeWord model on real recordings of "Hello Victoria" and set
`WAKE_WORD_MODEL_PATH` in `raspberry_pi/.env` — see
[docs/VOICE_PIPELINE.md](VOICE_PIPELINE.md#two-listening-strategies) for
why this can't be shipped pretrained.

## Verifying the end-to-end pipeline

1. On the Mini PC: `curl http://localhost:8000/health` → `{"status":"healthy",...}`
2. On the Pi: `python -m raspberry_pi.audio.diagnostics` → no warnings
3. On the Pi: `python -c "from raspberry_pi.client.connection import MiniPCClient; from raspberry_pi.config import get_config; print(MiniPCClient(get_config()).connect())"`
   → should print a `ConnectInfo` with a fresh `session_id`
4. Start the voice node and speak the wake phrase (or, in VAD-fallback
   mode, just speak) — check `logs/voice_node.log` on the Pi and
   `logs/victoria.log` on the Mini PC for the turn round trip.
