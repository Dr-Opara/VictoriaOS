from __future__ import annotations

from backend.core.logger import logger

PRIMARY_USER = "Dr Opara"


class SpeakerAuthenticator:
    """Restricts Victoria to responding to her primary user, Dr. Opara.

    ``authenticate`` checks an already-identified speaker name (used by the
    text-driven pipeline and tests). ``verify_audio`` is the hook for real
    voice-biometric verification: it requires an enrolled voiceprint and an
    embedding model (e.g. resemblyzer/pyannote), neither of which is wired
    up yet since it needs real enrollment audio from Dr. Opara. Until an
    embedding backend is configured it safely denies audio-based auth
    rather than pretending to verify a voice it never enrolled.
    """

    def authenticate(self, speaker: str) -> bool:
        """Return ``True`` if the identified speaker is the primary user."""
        return speaker == PRIMARY_USER

    def is_enrolled(self) -> bool:
        """Return ``True`` once a voiceprint has been enrolled for Dr. Opara."""
        return False

    def enroll(self, audio_samples: list[bytes]) -> None:
        """Enroll a voiceprint from sample audio clips (not yet implemented)."""
        raise NotImplementedError(
            "Voice enrollment requires an embedding backend (e.g. resemblyzer). "
            "Wire one up here before enabling audio-based speaker verification."
        )

    def verify_audio(self, audio: bytes) -> bool:
        """Verify a live audio clip against the enrolled voiceprint."""
        if not self.is_enrolled():
            logger.warning("Speaker verification attempted with no enrolled voiceprint.")
            return False

        raise NotImplementedError("Audio-based verification backend is not configured.")
