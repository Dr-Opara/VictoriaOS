"""Tests for the Mini PC voice API (backend/api/voice.py).

STT/GPT/TTS calls are monkeypatched onto the module's singleton service
instances so this suite never depends on live OpenAI access - it validates
the plumbing (routing, status codes, WS framing, format handling), not
model quality.
"""

from __future__ import annotations

import io
import wave

from fastapi.testclient import TestClient

from backend.api import voice as voice_api
from backend.app import app

client = TestClient(app)


def _wav_bytes(seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """A real (silent) WAV file, valid enough for format-level tests."""
    frame_count = int(seconds * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frame_count)
    return buffer.getvalue()


def _loud_pcm(seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    import numpy as np

    rng = np.random.default_rng(42)
    samples = rng.integers(-20000, 20000, int(seconds * sample_rate), dtype=np.int16)
    return samples.tobytes()


def test_voice_connect_returns_session_and_stream_params():
    response = client.get("/voice/connect")
    assert response.status_code == 200

    data = response.json()
    assert "session_id" in data
    assert data["wake_word"] == "hello victoria"
    assert data["sample_rate"] == 16000
    assert data["encoding"] == "pcm_s16le"


def test_voice_connect_returns_fresh_session_id_each_time():
    first = client.get("/voice/connect").json()["session_id"]
    second = client.get("/voice/connect").json()["session_id"]
    assert first != second


def test_voice_transcribe_returns_empty_for_silence(monkeypatch):
    monkeypatch.setattr(voice_api.speech_service, "transcribe", lambda audio, **kw: "")

    response = client.post(
        "/voice/transcribe", files={"audio": ("clip.wav", _wav_bytes(), "audio/wav")}
    )

    assert response.status_code == 200
    assert response.json() == {"transcript": ""}


def test_voice_transcribe_returns_recognized_text(monkeypatch):
    monkeypatch.setattr(
        voice_api.speech_service, "transcribe", lambda audio, **kw: "what's on my calendar"
    )

    response = client.post(
        "/voice/transcribe", files={"audio": ("clip.wav", _wav_bytes(), "audio/wav")}
    )

    assert response.status_code == 200
    assert response.json()["transcript"] == "what's on my calendar"


def test_voice_respond_returns_text_and_audio(monkeypatch):
    monkeypatch.setattr(
        voice_api.voice_engine.assistant,
        "think",
        lambda text, session_id: {"assistant": "Victoria", "response": "Here is your answer."},
    )
    monkeypatch.setattr(voice_api.tts_service, "synthesize", lambda text, fmt="wav": b"FAKEWAV")

    response = client.post(
        "/voice/respond", json={"text": "hello", "session_id": "test-respond"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Here is your answer."
    assert data["audio_base64"] is not None


def test_voice_respond_without_audio_flag_omits_audio(monkeypatch):
    monkeypatch.setattr(
        voice_api.voice_engine.assistant,
        "think",
        lambda text, session_id: {"assistant": "Victoria", "response": "ok"},
    )

    response = client.post(
        "/voice/respond",
        json={"text": "hello", "session_id": "test-respond-noaudio", "include_audio": False},
    )

    assert response.status_code == 200
    assert response.json()["audio_base64"] is None


def test_voice_command_returns_unrecognized_for_silent_file(monkeypatch):
    # File uploads (unlike raw PCM streamed over WS) can be any container/
    # codec, so silence detection can't run VAD on the raw bytes - it's
    # caught by STT returning an empty transcript instead. See the
    # process_audio docstring in backend/voice/engine.py.
    monkeypatch.setattr(voice_api.voice_engine.speech, "transcribe", lambda audio, **kw: "")

    response = client.post(
        "/voice/command", files={"audio": ("clip.wav", _wav_bytes(), "audio/wav")}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "unrecognized"


def test_voice_command_returns_audio_when_awake(monkeypatch):
    monkeypatch.setattr(voice_api.voice_engine.speech, "transcribe", lambda audio, **kw: "hello victoria what time is it")
    monkeypatch.setattr(
        voice_api.voice_engine.assistant,
        "think",
        lambda text, session_id: {"assistant": "Victoria", "response": "It's noon."},
    )
    monkeypatch.setattr(voice_api.voice_engine.tts, "synthesize", lambda text, response_format="mp3": b"FAKEAUDIO")

    response = client.post(
        "/voice/command",
        files={"audio": ("clip.wav", _loud_pcm(), "audio/wav")},
        params={"session_id": "test-command-audio"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"FAKEAUDIO"


def test_voice_stream_connect_ping_pong():
    with client.websocket_connect("/voice/stream") as ws:
        greeting = ws.receive_json()
        assert greeting["event"] == "connected"

        ws.send_json({"event": "ping"})
        pong = ws.receive_json()
        assert pong["event"] == "pong"


def test_voice_stream_end_of_turn_with_silence_reports_silence():
    silence = b"\x00\x00" * 16000

    with client.websocket_connect("/voice/stream?session_id=test-ws-silence") as ws:
        ws.receive_json()
        ws.send_bytes(silence)
        ws.send_json({"event": "end_of_turn"})
        result = ws.receive_json()

    assert result["event"] == "result"
    assert result["status"] == "silence"
    assert "latency_ms" in result


def test_voice_stream_end_of_turn_wraps_pcm_and_produces_reply(monkeypatch):
    monkeypatch.setattr(voice_api.voice_engine.speech, "transcribe", lambda audio, **kw: "hello victoria")
    monkeypatch.setattr(
        voice_api.voice_engine.assistant,
        "think",
        lambda text, session_id: {"assistant": "Victoria", "response": "Hi there."},
    )
    monkeypatch.setattr(voice_api.voice_engine.tts, "synthesize", lambda text, response_format="mp3": b"REPLYAUDIO")

    with client.websocket_connect("/voice/stream?session_id=test-ws-reply") as ws:
        ws.receive_json()
        ws.send_bytes(_loud_pcm())
        ws.send_json({"event": "end_of_turn"})
        result = ws.receive_json()
        assert result["status"] == "awake"
        assert result["transcript"] == "hello victoria"

        reply_audio = ws.receive_bytes()
        assert reply_audio == b"REPLYAUDIO"


def test_voice_stream_rejects_missing_api_key(monkeypatch):
    from backend.config.settings import get_settings

    get_settings.cache_clear()
    original_api_key = voice_api.get_settings().api_key
    voice_api.get_settings().api_key = "secret-for-ws-test"
    try:
        with client.websocket_connect("/voice/stream") as ws:
            ws.receive_json()
        assert False, "expected the connection to be rejected"
    except Exception:
        pass
    finally:
        voice_api.get_settings().api_key = original_api_key
