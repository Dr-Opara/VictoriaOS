"""The voice node: ties audio capture, wake word, VAD, streaming, and
playback into the running service.

    Mic -> (wake word | VAD fallback) -> Pi Client -> Mini PC /voice/stream
        -> GPT-5 -> Mini PC response -> Pi Speaker

Run as the systemd service (see ``raspberry_pi/systemd/victoria-voice.service``):

    python -m raspberry_pi.client.voice_node
"""

from __future__ import annotations

import time

from raspberry_pi.audio.microphone import Microphone
from raspberry_pi.audio.speaker import Speaker
from raspberry_pi.audio.vad import EndpointDetector, VoiceActivityDetector
from raspberry_pi.client.connection import MiniPCClient, VoiceStreamClient
from raspberry_pi.config import PiConfig, get_config
from raspberry_pi.health.monitor import HealthMonitor
from raspberry_pi.logging_config import get_logger
from raspberry_pi.wakeword.factory import create_wakeword_engine

logger = get_logger()


class VoiceNode:
    """The Pi-side voice pipeline: listen, stream a turn, speak the reply.

    Two listening strategies, chosen automatically:

    - **Local wake word** (preferred): if a trained openWakeWord model is
      configured, the node stays in a low-CPU listening loop and only opens
      a streaming turn after the wake word fires locally.
    - **VAD fallback**: if no trained model is available, the node starts a
      turn on any detected speech and relies on the Mini PC's existing
      text-based wake-word gate (after STT) to decide whether "Hello
      Victoria" was actually said. This means every utterance is sent to
      the Mini PC rather than filtered locally - higher network/API use,
      but fully functional without a custom-trained model.
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

        if self.wakeword_engine.is_ready:
            logger.info("Voice node listening strategy: local wake word.")
        else:
            logger.info(
                "Voice node listening strategy: VAD fallback "
                "(no trained wake-word model configured)."
            )

    def run(self) -> None:
        """Run the voice node forever: connect, listen, converse, reconnect."""
        connect_info = self.rest_client.connect_with_backoff(
            self.config.reconnect_initial_delay_seconds,
            self.config.reconnect_max_delay_seconds,
        )
        logger.info("Connected to Mini PC. Session: %s", connect_info.session_id)

        health_monitor = HealthMonitor(self.config, self.rest_client)
        health_monitor.start()

        try:
            while True:
                self._run_session(connect_info.session_id)
                logger.warning("Voice stream session ended; reconnecting.")
        finally:
            health_monitor.stop()

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
                recording = bytearray()
                turn_started_at: float | None = None

                for chunk in mic.chunks():
                    if self.wakeword_engine.is_ready:
                        if not self._triggered(chunk):
                            continue
                        self.wakeword_engine.reset()
                        logger.info("Wake word detected.")
                        turn_started_at = time.monotonic()
                        endpoint.reset()
                        recording = bytearray()

                    if turn_started_at is None:
                        if not self.vad.is_speech(chunk):
                            continue
                        turn_started_at = time.monotonic()
                        endpoint.reset()
                        recording = bytearray()

                    recording.extend(chunk)
                    stream.send_audio(chunk)

                    timed_out = (
                        time.monotonic() - turn_started_at > self.config.max_utterance_seconds
                    )
                    if endpoint.push(chunk) or timed_out:
                        stream.end_of_turn()
                        result, audio = stream.receive_turn_result()
                        self._handle_result(result, audio, speaker)
                        turn_started_at = None
                        recording = bytearray()

    def _triggered(self, chunk: bytes) -> bool:
        return self.wakeword_engine.process(chunk) >= self.config.wake_word_threshold

    def _handle_result(self, result: dict, audio: bytes | None, speaker: Speaker) -> None:
        status = result.get("status")
        logger.info("Turn result: status=%s transcript=%r", status, result.get("transcript"))

        if status == "denied":
            logger.warning("Speaker verification denied this request.")

        if audio:
            speaker.play(audio)


def main() -> None:
    node = VoiceNode()
    node.run()


if __name__ == "__main__":
    main()
