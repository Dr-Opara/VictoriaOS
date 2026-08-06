# VictoriaOS Voice Node (Raspberry Pi)

The Raspberry Pi-side half of the VictoriaOS voice pipeline. See
[docs/VOICE_PIPELINE.md](../docs/VOICE_PIPELINE.md) for the full protocol
and [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) for setup instructions.

```
raspberry_pi/
  audio/        Device discovery, microphone capture, speaker playback, VAD, diagnostics
  wakeword/      Pluggable wake-word engine (openWakeWord + graceful no-op fallback)
  client/        HTTP + WebSocket client for the Mini PC, and the VoiceNode orchestrator
  health/        Heartbeat/health monitoring
  systemd/       systemd unit for running as a service
  config.py      Environment-driven configuration
  logging_config.py
```

Quick start:

```bash
python -m venv .venv-pi && source .venv-pi/bin/activate
sudo apt install -y libportaudio2
pip install -r raspberry_pi/requirements.txt
cp raspberry_pi/.env.example raspberry_pi/.env   # edit MINI_PC_URL, API_KEY
python -m raspberry_pi.audio.diagnostics          # verify hardware first
python -m raspberry_pi.client.voice_node          # run it
```

This package never imports OpenAI or calls GPT directly — everything flows
through the Mini PC's `/voice/*` API (`raspberry_pi/client/connection.py`).
