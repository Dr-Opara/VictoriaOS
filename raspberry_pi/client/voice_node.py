"""The voice node: ties audio capture, wake word, VAD, streaming, and
playback into the running service.

    Mic -> (wake word | push-to-talk | VAD fallback) -> Pi Client
        -> Mini PC /voice/stream -> GPT-5 -> Mini PC response -> Pi Speaker

Run directly for testing:

    python -m raspberry_pi.client.voice_node

Run as the systemd service for production (see
``raspberry_pi/systemd/victoria-voice.service`` and
``docs/DEPLOYMENT.md``).
"""

from __future__ import annotations

import time

from raspberry_pi.audio.microphone import Microphone, MicrophoneDisconnectedError
from raspberry_pi.audio.speaker import Speaker, SpeakerDisconnectedError
from raspberry_pi.audio.vad import EndpointDetector, VoiceActivityDetector
from raspberry_pi.client.connection import MiniPCClient, VoiceStreamClient
from raspberry_pi.client.push_to_talk import PushToTalkTrigger
from raspberry_pi.config import PiConfig, get_config
from raspberry_pi.health.monitor import HealthMonitor
from raspberry_pi.logging_config import get_logger
from raspberry_pi.wakeword.factory import create_wakeword_engine

logger = get_logger()

# How long to back off after a recoverable in-session error (device dropout,
# transient network failure) before starting a fresh session, so a flapping
# device/link doesn't spin the CPU in a tight retry loop.
_SESSION_ERROR_BACKOFF_SECONDS = 3.0


class VoiceNode:
    """The Pi-side voice pipeline: listen, stream a turn, speak the reply.

    Three listening strategies, chosen automatically (see docs/VOICE_PIPELINE.md):

    - **Local wake word** (preferred): if a trained openWakeWord model is
      configured, the node stays in a low-CPU listening loop and only opens
      a streaming turn after the wake word fires locally.
    - **Push-to-talk** (testing only): if ``PUSH_TO_TALK=true``, press Enter
      in an interactive terminal to start a turn.
    - **VAD fallback**: otherwise, the node starts a turn on any detected
      speech and relies on the Mini PC's existing text-based wake-word gate
      (after STT) to decide whether "Hello Victoria" was actually said.
    """

    def __init__(self, config: PiConfig | None = None) -> None:
        self.config = config or get_config()
        self.wakeword_engine = create_wakeword_engine(self.config)
        self.rest_client = MiniPCClient(self.config)
        self.vad = VoiceActivityDetector(
            sample_rate=self.config.sample_rate,
            frame_ms=self.config.frame_ms,
            energy_threshold=self.config.vad_energy_threshold,
            silence_hold_ms=self.config.silence_timeout_ms,
        )
        self.push_to_talk = PushToTalkTrigger() if self.config.push_to_talk else None

        if self.config.push_to_talk:
            logger.info("Voice node listening strategy: push-to-talk (TEST MODE).")
        elif self.wakeword_engine.is_ready:
            logger.info("Voice node listening strategy: local wake word.")
        else:
            logger.warning(
                "Voice node listening strategy: VAD fallback - no trained wake-word "
                "model is configured (WAKE_WORD_MODEL_PATH is unset or the file is "
                "missing). Every detected utterance will be streamed to the Mini PC; "
                "wake-word gating happens server-side after transcription. See "
                "docs/VOICE_PIPELINE.md to train a model, or set PUSH_TO_TALK=true "
                "for manual testing."
            )

    def run(self) -> None:
        """Run the voice node forever: connect, listen, converse, reconnect."""
        if self.push_to_talk:
            self.push_to_talk.start()

        logger.info("Connecting to Mini PC at %s ...", self.config.mini_pc_url)
        connect_info = self.rest_client.connect_with_backoff(
            self.config.reconnect_initial_delay_seconds,
            self.config.reconnect_max_delay_seconds,
        )
        logger.info("Connected to Mini PC. Session: %s", connect_info.session_id)

        health_monitor = HealthMonitor(self.config, self.rest_client)
        health_monitor.start()

        try:
            while True:
                try:
                    self._run_session(connect_info.session_id)
                except MicrophoneDisconnectedError:
                    logger.error(
                        "Microphone disconnected. Retrying device selection in %.0fs - "
                        "check the microphone is plugged in.",
                        _SESSION_ERROR_BACKOFF_SECONDS,
                    )
                    time.sleep(_SESSION_ERROR_BACKOFF_SECONDS)
                except SpeakerDisconnectedError:
                    logger.error(
                        "Speaker disconnected. Retrying device selection in %.0fs - "
                        "check the speaker is plugged in.",
                        _SESSION_ERROR_BACKOFF_SECONDS,
                    )
                    time.sleep(_SESSION_ERROR_BACKOFF_SECONDS)
                except OSError as error:
                    logger.error(
                        "Voice stream session error (%s). Mini PC may be offline; "
                        "reconnecting.",
                        error,
                    )

                logger.warning("Voice stream session ended; reconnecting.")
        finally:
            health_monitor.stop()
            if self.push_to_talk:
                self.push_to_talk.stop()

    def _run_session(self, session_id: str) -> None:
        stream_client = VoiceStreamClient(self.config, session_id)
        speaker = Speaker(device_hint=self.config.output_device_hint)

        with stream_client.connected() as stream:
            with Microphone(
                sample_rate=self.config.sample_rate,
                channels=self.config.channels,
                frame_ms=self.config.frame_ms,
                device_hint=self.config.input_device_hint,
            ) as mic:
                endpoint = EndpointDetector(self.vad)
                turn_started_at: float | None = None

                for chunk in mic.chunks():
                    if speaker.is_playing:
                        self._watch_for_interruption(chunk, speaker)
                        continue

                    if turn_started_at is None:
                        if not self._should_start_turn(chunk):
                            continue
                        logger.info("Turn started.")
                        turn_started_at = time.monotonic()
                        endpoint.reset()
                        # Drop any backlog from before the trigger, but still
                        # send this triggering chunk itself below - it's
                        # part of the utterance, not stale audio.
                        mic.drain()

                    stream.send_audio(chunk)

                    timed_out = (
                        time.monotonic() - turn_started_at > self.config.max_utterance_seconds
                    )
                    if timed_out:
                        logger.warning(
                            "Max utterance length (%.0fs) reached; ending turn.",
                            self.config.max_utterance_seconds,
                        )
                    if endpoint.push(chunk) or timed_out:
                        stream.end_of_turn()
                        result, audio = stream.receive_turn_result(
                            timeout=self.config.request_timeout_seconds
                        )
                        self._handle_result(result, audio, speaker)
                        mic.drain()
                        turn_started_at = None

    def _should_start_turn(self, chunk: bytes) -> bool:
        """Decide whether this chunk should begin a new turn, per the active strategy."""
        if self.push_to_talk:
            return self.push_to_talk.consume()

        if self.wakeword_engine.is_ready:
            if self.wakeword_engine.process(chunk) >= self.config.wake_word_threshold:
                self.wakeword_engine.reset()
                logger.info("Wake word detected.")
                return True
            return False

        return self.vad.is_speech(chunk)

    def _watch_for_interruption(self, chunk: bytes, speaker: Speaker) -> None:
        """While Victoria is speaking, stop playback if the user starts talking."""
        if self.vad.is_speech(chunk):
            logger.info("Interruption detected; stopping playback.")
            speaker.stop()

    def _handle_result(self, result: dict, audio: bytes | None, speaker: Speaker) -> None:
        status = result.get("status")
        logger.info("Turn result: status=%s transcript=%r", status, result.get("transcript"))

        if status == "denied":
            logger.warning("Speaker verification denied this request.")
        elif status in ("silence", "unrecognized"):
            logger.info("Nothing actionable in this turn (%s).", status)

        if audio:
            speaker.play(audio, block=False)


def main() -> None:
    node = VoiceNode()
    node.run()


if __name__ == "__main__":
    main()
