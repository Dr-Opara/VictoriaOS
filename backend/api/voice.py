from __future__ import annotations

from fastapi import APIRouter, UploadFile
from fastapi.responses import Response

from backend.voice.engine import VoiceEngine

router = APIRouter(prefix="/voice", tags=["Voice"])
voice_engine = VoiceEngine()


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
