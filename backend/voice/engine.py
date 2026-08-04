from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from backend.core.assistant import VictoriaAssistant
from backend.core.logger import logger
from backend.voice.speaker import SpeakerAuthenticator
from backend.voice.speech import SpeechService
from backend.voice.tts import TextToSpeech
from backend.voice.vad import VoiceActivityDetector
from backend.voice.wakeword import WakeWordDetector

CONVERSATION_TIMEOUT_SECONDS = 15.0


class ConversationState(str, Enum):
    SLEEPING = "sleeping"
    AWAKE = "awake"
    SPEAKING = "speaking"


@dataclass
class ConversationSession:
    """Tracks Victoria's voice state for one user across turns.

    Once woken by "Hello Victoria", the session stays ``AWAKE`` so the user
    can have a multi-turn conversation without repeating the wake word,
    until ``CONVERSATION_TIMEOUT_SECONDS`` of silence elapses.
    """

    session_id: str = "voice-default"
    state: ConversationState = ConversationState.SLEEPING
    last_activity: float = field(default_factory=time.monotonic)

    def touch(self) -> None:
        self.last_activity = time.monotonic()

    def is_timed_out(self) -> bool:
        return (time.monotonic() - self.last_activity) > CONVERSATION_TIMEOUT_SECONDS

    def wake(self) -> None:
        self.state = ConversationState.AWAKE
        self.touch()

    def sleep(self) -> None:
        self.state = ConversationState.SLEEPING

    def start_speaking(self) -> None:
        self.state = ConversationState.SPEAKING

    def interrupt(self) -> None:
        """Called when new speech is detected while Victoria is speaking."""
        if self.state == ConversationState.SPEAKING:
            logger.info("Voice interruption detected; stopping playback.")
            self.state = ConversationState.AWAKE
            self.touch()


class VoiceEngine:
    """Controls the complete voice pipeline: wake word through spoken reply.

    Pipeline: VAD end-points a speech segment -> STT transcribes it -> the
    wake word (or an already-awake session) gates access -> speaker
    verification restricts responses to Dr. Opara -> the transcript is
    routed through VictoriaAssistant (which itself flows through the AI
    Context Builder) -> the reply is synthesized back to audio.
    """

    def __init__(
        self,
        assistant: VictoriaAssistant | None = None,
        wakeword: WakeWordDetector | None = None,
        auth: SpeakerAuthenticator | None = None,
        vad: VoiceActivityDetector | None = None,
        speech: SpeechService | None = None,
        tts: TextToSpeech | None = None,
    ) -> None:
        self.assistant = assistant or VictoriaAssistant()
        self.wakeword = wakeword or WakeWordDetector()
        self.auth = auth or SpeakerAuthenticator()
        self.vad = vad or VoiceActivityDetector()
        self.speech = speech or SpeechService()
        self.tts = tts or TextToSpeech()
        self._sessions: dict[str, ConversationSession] = {}

    def _session(self, session_id: str) -> ConversationSession:
        session = self._sessions.setdefault(session_id, ConversationSession(session_id))
        if session.state == ConversationState.AWAKE and session.is_timed_out():
            logger.info("Voice session %s timed out; returning to sleep.", session_id)
            session.sleep()
        return session

    def process(self, text: str, session_id: str = "voice-default") -> dict[str, Any]:
        """Process already-transcribed text through the wake/auth/assistant flow.

        Kept for text-driven callers (tests, the ``/voice`` debug endpoint).
        For real audio, use ``process_audio``.
        """
        session = self._session(session_id)

        if session.state == ConversationState.SLEEPING and not self.wakeword.detect(text):
            return {"status": "sleeping"}

        if not self.auth.authenticate("Dr Opara"):
            return {
                "status": "denied",
                "message": "I am only programmed to respond to Dr Opara.",
            }

        if session.state == ConversationState.SLEEPING:
            session.wake()
            command = self.wakeword.strip_wake_word(text)
            if not command:
                return {
                    "status": "awake",
                    "message": "Hello Dr. Opara, what can I help you with today?",
                }
        else:
            session.touch()
            command = text

        session.start_speaking()
        result = self.assistant.think(command, session_id=session_id)
        session.wake()

        return {"status": "awake", "message": result["response"]}

    def process_audio(self, audio: bytes, session_id: str = "voice-default") -> dict[str, Any]:
        """Run the full audio pipeline: VAD -> STT -> wake/auth -> reply audio."""
        session = self._session(session_id)

        if not self.vad.is_speech(audio):
            return {"status": "silence"}

        if session.state == ConversationState.SPEAKING:
            session.interrupt()

        text = self.speech.transcribe(audio)
        if not text:
            return {"status": "unrecognized"}

        result = self.process(text, session_id=session_id)
        if result.get("status") == "awake":
            result["audio"] = self.tts.synthesize(result["message"])

        return result
