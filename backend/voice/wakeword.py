from __future__ import annotations


class WakeWordDetector:
    """Detects Victoria's wake word, "Hello Victoria".

    Detection runs on the text transcribed by ``SpeechService`` rather than
    on raw audio. This keeps the pipeline simple (no extra native wake-word
    model/dependency such as Porcupine) while still supporting hands-free
    activation: audio is continuously transcribed in short chunks and each
    transcript is checked against the wake phrase.
    """

    WAKE_WORD = "hello victoria"

    def detect(self, text: str) -> bool:
        """Return ``True`` if the wake word appears in ``text``."""
        return self.WAKE_WORD in text.lower()

    def strip_wake_word(self, text: str) -> str:
        """Remove the wake word from ``text``, returning the remaining command."""
        lowered = text.lower()
        index = lowered.find(self.WAKE_WORD)
        if index == -1:
            return text.strip()

        return (text[:index] + text[index + len(self.WAKE_WORD):]).strip(" ,.")
