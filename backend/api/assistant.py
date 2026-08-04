from fastapi import APIRouter

from backend.core.assistant import VictoriaAssistant

router = APIRouter(prefix="/assistant", tags=["Assistant"])

assistant = VictoriaAssistant()


@router.get("/think")
def think(command: str, session_id: str = "default"):
    return assistant.think(command, session_id=session_id)
