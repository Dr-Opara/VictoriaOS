"""Runtime configuration for the Raspberry Pi voice node.

Kept dependency-free (stdlib only) so it can be imported before checking
whether optional hardware/ML dependencies (sounddevice, openwakeword) are
even installed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class PiConfig:
    """Configuration for the voice node, sourced from the environment."""

    mini_pc_url: str = field(default_factory=lambda: os.getenv("MINI_PC_URL", "http://localhost:8000"))
    api_key: str = field(default_factory=lambda: os.getenv("API_KEY", ""))

    input_device_hint: str = field(
        default_factory=lambda: os.getenv("INPUT_DEVICE_HINT", "respeaker,seeed,usb")
    )
    output_device_hint: str = field(
        default_factory=lambda: os.getenv("OUTPUT_DEVICE_HINT", "")
    )

    sample_rate: int = field(default_factory=lambda: int(os.getenv("SAMPLE_RATE", "16000")))
    channels: int = field(default_factory=lambda: int(os.getenv("CHANNELS", "1")))
    frame_ms: int = field(default_factory=lambda: int(os.getenv("FRAME_MS", "30")))

    vad_energy_threshold: float = field(
        default_factory=lambda: float(os.getenv("VAD_ENERGY_THRESHOLD", "500"))
    )
    silence_timeout_ms: int = field(
        default_factory=lambda: int(os.getenv("SILENCE_TIMEOUT_MS", "800"))
    )
    max_utterance_seconds: float = field(
        default_factory=lambda: float(os.getenv("MAX_UTTERANCE_SECONDS", "20"))
    )

    wake_word_phrase: str = field(default_factory=lambda: os.getenv("WAKE_WORD_PHRASE", "hello victoria"))
    wake_word_model_path: str = field(default_factory=lambda: os.getenv("WAKE_WORD_MODEL_PATH", ""))
    wake_word_threshold: float = field(
        default_factory=lambda: float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))
    )

    conversation_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("CONVERSATION_TIMEOUT_SECONDS", "15"))
    )
    heartbeat_interval_seconds: float = field(
        default_factory=lambda: float(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "10"))
    )
    reconnect_initial_delay_seconds: float = field(
        default_factory=lambda: float(os.getenv("RECONNECT_INITIAL_DELAY_SECONDS", "1"))
    )
    reconnect_max_delay_seconds: float = field(
        default_factory=lambda: float(os.getenv("RECONNECT_MAX_DELAY_SECONDS", "30"))
    )

    speaker_verification_enabled: bool = field(
        default_factory=lambda: _bool_env("SPEAKER_VERIFICATION_ENABLED", False)
    )

    log_dir: str = field(default_factory=lambda: os.getenv("VOICE_NODE_LOG_DIR", "logs"))


def get_config() -> PiConfig:
    """Return a fresh :class:`PiConfig` read from the current environment."""
    return PiConfig()
