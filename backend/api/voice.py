from __future__ import annotations

import base64
import json
import time
import uuid

from fastapi import APIRouter, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from backend.config.settings import get_settings
from backend.core.logger import logger
from backend.voice.engine import VoiceEngine
from backend.voice.speech import SpeechService
from backend.voice.tts import SupportedAudioFormat, TextToSpeech

router = APIRouter(prefix="/voice", tags=["Voice"])
voice_engine = VoiceEngine()
speech_service = SpeechService()
tts_service = TextToSpeech()


@router.get("/text")
def voice_text(text: str, session_id: str = "voice-default"):
    """Debug entry point: run the wake/auth/assistant flow on plain text."""
    return voice_engine.process(text, session_id=session_id)


@router.post("/command")
async def voice_command(audio: UploadFile, session_id: str = "voice-default"):
    """Run the full voice pipeline on an uploaded audio clip.

    Returns Victoria's spoken reply as audio when she responds, otherwise a
    status payload (sleeping/denied/silence/unrecognized).
    """
    audio_bytes = await audio.read()
    result = voice_engine.process_audio(audio_bytes, session_id=session_id)

    reply_audio = result.pop("audio", None)
    if reply_audio:
        return Response(content=reply_audio, media_type="audio/mpeg")

    return result


@router.get("/connect")
def voice_connect():
    """Handshake endpoint for voice nodes (e.g. the Raspberry Pi client).

    Returns a fresh session id and the parameters a client needs to stream
    audio correctly (sample format, wake word). Voice nodes should call this
    once on startup/reconnect, then open ``WS /voice/stream`` using the
    returned ``session_id``.
    """
    return {
        "session_id": str(uuid.uuid4()),
        "wake_word": voice_engine.wakeword.WAKE_WORD,
        "sample_rate": 16000,
        "sample_width_bytes": 2,
        "channels": 1,
        "encoding": "pcm_s16le",
    }


class TranscribeResponse(BaseModel):
    transcript: str


@router.post("/transcribe", response_model=TranscribeResponse)
async def voice_transcribe(audio: UploadFile):
    """Transcribe an audio clip to text without running it through Victoria."""
    audio_bytes = await audio.read()
    transcript = await run_in_threadpool(speech_service.transcribe, audio_bytes)
    return TranscribeResponse(transcript=transcript)


class RespondRequest(BaseModel):
    text: str
    session_id: str = "voice-default"
    include_audio: bool = True
    audio_format: SupportedAudioFormat = "wav"


class RespondResponse(BaseModel):
    response: str
    audio_base64: str | None = None


@router.post("/respond", response_model=RespondResponse)
async def voice_respond(request: RespondRequest):
    """Take already-transcribed text, run it through Victoria, and speak the reply.

    Unlike ``/voice/text``/``/voice/command``, this always answers (no wake
    word gate) — useful for clients that have already decided the utterance
    is directed at Victoria (e.g. after their own wake-word/VAD gating).
    """
    result = await run_in_threadpool(
        voice_engine.assistant.think, request.text, request.session_id
    )
    response_text = result["response"]

    audio_base64 = None
    if request.include_audio:
        audio_bytes = await run_in_threadpool(
            tts_service.synthesize, response_text, request.audio_format
        )
        audio_base64 = base64.b64encode(audio_bytes).decode("ascii")

    return RespondResponse(response=response_text, audio_base64=audio_base64)


@router.websocket("/stream")
async def voice_stream(websocket: WebSocket):
    """Duplex audio streaming channel for voice nodes.

    Protocol: the client sends binary frames containing raw audio chunks as
    they're captured, then a text frame ``{"event": "end_of_turn"}`` once its
    own VAD has end-pointed the utterance. The server buffers the chunks,
    runs the full voice pipeline on the assembled clip, and replies with a
    text frame (``{"event": "result", ...}``) followed by a binary frame
    with the synthesized reply audio, when there is one to speak.
    """
    settings = get_settings()
    if settings.api_key and websocket.query_params.get("api_key") != settings.api_key:
        # BaseHTTPMiddleware (ApiKeyMiddleware) never runs for websocket scope,
        # so the check has to happen here for this route specifically.
        logger.warning("Rejected voice stream connection: missing/invalid API key.")
        await websocket.close(code=4401, reason="Invalid or missing API key.")
        return

    await websocket.accept()
    session_id = websocket.query_params.get("session_id") or str(uuid.uuid4())
    logger.info("Voice stream connected: session_id=%s", session_id)
    await websocket.send_json({"event": "connected", "session_id": session_id})

    audio_buffer = bytearray()

    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            audio_chunk = message.get("bytes")
            if audio_chunk is not None:
                audio_buffer.extend(audio_chunk)
                continue

            text_payload = message.get("text")
            if text_payload is None:
                continue

            try:
                event = json.loads(text_payload)
            except json.JSONDecodeError:
                logger.warning("Ignoring malformed voice stream frame from %s", session_id)
                continue

            event_type = event.get("event")

            if event_type == "ping":
                await websocket.send_json({"event": "pong", "server_time": time.time()})
                continue

            if event_type == "reset":
                audio_buffer.clear()
                continue

            if event_type == "end_of_turn":
                utterance = bytes(audio_buffer)
                audio_buffer.clear()

                start_time = time.monotonic()
                result = await run_in_threadpool(
                    voice_engine.process_audio,
                    utterance,
                    session_id,
                    "wav",
                    "pcm",
                )
                elapsed_ms = (time.monotonic() - start_time) * 1000

                reply_audio = result.pop("audio", None)
                logger.info(
                    "Voice stream turn | session_id=%s status=%s latency_ms=%.1f",
                    session_id,
                    result.get("status"),
                    elapsed_ms,
                )
                await websocket.send_json({"event": "result", "latency_ms": elapsed_ms, **result})

                if reply_audio:
                    await websocket.send_bytes(reply_audio)

    except WebSocketDisconnect:
        logger.info("Voice stream disconnected: session_id=%s", session_id)
