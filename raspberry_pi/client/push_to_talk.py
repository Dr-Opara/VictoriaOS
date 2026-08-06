"""Push-to-talk: a temporary testing fallback for when no wake-word model is
trained and you want to test the pipeline without VAD triggering on every
sound in the room.

This is intentionally simple: press Enter in the terminal to start a turn,
then speak - the turn ends the same way any other turn does (silence
timeout or max utterance length). It is not meant as the production
trigger; it exists so the rest of the pipeline (streaming, STT, GPT,
TTS, playback) can be exercised on hardware without a trained wake-word
model and without the higher false-trigger rate of pure VAD-fallback mode.
"""

from __future__ import annotations

import sys
import threading

from raspberry_pi.logging_config import get_logger

logger = get_logger()


class PushToTalkTrigger:
    """Watches stdin for Enter presses on a background thread."""

    def __init__(self) -> None:
        self._event = threading.Event()
        self._thread: threading.Thread | None = None
        self._stop = False

    def start(self) -> None:
        self._thread = threading.Thread(target=self._watch_stdin, daemon=True)
        self._thread.start()
        logger.info("Push-to-talk test mode active: press Enter, then speak.")

    def stop(self) -> None:
        self._stop = True

    def _watch_stdin(self) -> None:
        while not self._stop:
            try:
                line = sys.stdin.readline()
            except (OSError, ValueError):  # pragma: no cover - no interactive stdin
                logger.warning("Push-to-talk: stdin is not available; disabling trigger.")
                return
            if not line:  # EOF - stdin closed (e.g. running under systemd)
                logger.warning(
                    "Push-to-talk: stdin closed. This mode requires an interactive "
                    "terminal; run the voice node manually (not via systemd) to use it."
                )
                return
            self._event.set()

    def consume(self) -> bool:
        """Return True and clear the trigger if Enter was pressed since the last check."""
        if self._event.is_set():
            self._event.clear()
            return True
        return False
