"""Health monitoring: periodic heartbeat + component status checks.

Detects the failure modes called out for the voice node: Mini PC offline,
microphone unplugged, speaker unavailable. ("Pi offline" and "OpenAI
unavailable" are, by definition, checked from the *other* side - the Mini
PC already reports its own OpenAI reachability via ``/system/status``, and
"Pi offline" is simply the Mini PC no longer receiving this heartbeat.)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum

from raspberry_pi.audio.devices import AudioBackendUnavailable, list_input_devices, list_output_devices
from raspberry_pi.client.connection import MiniPCClient
from raspberry_pi.config import PiConfig
from raspberry_pi.logging_config import get_logger

logger = get_logger()


class ComponentStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class HealthSnapshot:
    timestamp: float
    mini_pc: ComponentStatus
    microphone: ComponentStatus
    speaker: ComponentStatus

    @property
    def healthy(self) -> bool:
        return all(
            status == ComponentStatus.OK
            for status in (self.mini_pc, self.microphone, self.speaker)
        )


def check_mini_pc(client: MiniPCClient) -> ComponentStatus:
    return ComponentStatus.OK if client.health() else ComponentStatus.UNAVAILABLE


def check_microphone() -> ComponentStatus:
    try:
        return ComponentStatus.OK if list_input_devices() else ComponentStatus.UNAVAILABLE
    except AudioBackendUnavailable:
        return ComponentStatus.UNAVAILABLE


def check_speaker() -> ComponentStatus:
    try:
        return ComponentStatus.OK if list_output_devices() else ComponentStatus.UNAVAILABLE
    except AudioBackendUnavailable:
        return ComponentStatus.UNAVAILABLE


def snapshot(client: MiniPCClient) -> HealthSnapshot:
    """Take one health snapshot across all monitored components."""
    return HealthSnapshot(
        timestamp=time.time(),
        mini_pc=check_mini_pc(client),
        microphone=check_microphone(),
        speaker=check_speaker(),
    )


class HealthMonitor:
    """Runs periodic health snapshots and logs/reacts to state transitions."""

    def __init__(self, config: PiConfig, client: MiniPCClient) -> None:
        self.config = config
        self.client = client
        self._last: HealthSnapshot | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start polling health in a background thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background polling thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self.config.heartbeat_interval_seconds + 1)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            current = snapshot(self.client)
            self._report_transition(current)
            self._last = current
            self._stop_event.wait(self.config.heartbeat_interval_seconds)

    def _report_transition(self, current: HealthSnapshot) -> None:
        if self._last is None:
            logger.info("Health check | %s", current)
            return

        for field_name in ("mini_pc", "microphone", "speaker"):
            previous_value = getattr(self._last, field_name)
            current_value = getattr(current, field_name)
            if previous_value != current_value:
                logger.warning(
                    "Health transition | %s: %s -> %s", field_name, previous_value, current_value
                )
