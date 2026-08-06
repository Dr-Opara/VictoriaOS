"""Audio subsystem diagnostics: device discovery report + live input level check.

Run directly for a human-readable report:

    python -m raspberry_pi.audio.diagnostics
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass

import numpy as np

from raspberry_pi.audio.devices import (
    AudioBackendUnavailable,
    get_sounddevice_backend,
    list_input_devices,
    list_output_devices,
    select_input_device,
    select_output_device,
)
from raspberry_pi.config import get_config
from raspberry_pi.logging_config import get_logger

logger = get_logger()


@dataclass
class DiagnosticsReport:
    backend_available: bool
    error: str | None
    input_device_count: int
    output_device_count: int
    selected_input: str | None
    selected_output: str | None
    input_peak_level: float | None
    warnings: list[str]


def measure_input_level(device_index: int, sample_rate: int = 16000, duration_seconds: float = 1.0, sd_module=None) -> float:
    """Record briefly from ``device_index`` and return the peak amplitude (0-1)."""
    sd = sd_module or get_sounddevice_backend()
    recording = sd.rec(
        int(duration_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        device=device_index,
    )
    sd.wait()
    peak = float(np.max(np.abs(recording))) / 32768.0
    return peak


def run_diagnostics(measure_level: bool = True) -> DiagnosticsReport:
    """Run a full audio subsystem diagnostic sweep."""
    config = get_config()
    warnings: list[str] = []

    try:
        sd = get_sounddevice_backend()
    except AudioBackendUnavailable as error:
        return DiagnosticsReport(
            backend_available=False,
            error=str(error),
            input_device_count=0,
            output_device_count=0,
            selected_input=None,
            selected_output=None,
            input_peak_level=None,
            warnings=[],
        )

    inputs = list_input_devices(sd)
    outputs = list_output_devices(sd)

    if not inputs:
        warnings.append("No input devices detected - microphone unplugged?")
    if not outputs:
        warnings.append("No output devices detected - speaker unavailable?")

    selected_input = None
    selected_output = None
    peak_level = None

    if inputs:
        device = select_input_device(config.input_device_hint, sd_module=sd)
        selected_input = device.name
        if measure_level:
            try:
                peak_level = measure_input_level(device.index, sd_module=sd)
                if peak_level < 0.01:
                    warnings.append(
                        f"Input level from {device.name!r} is near-silent "
                        f"(peak={peak_level:.4f}) - check the microphone is unmuted."
                    )
            except Exception as error:  # pragma: no cover - hardware dependent
                warnings.append(f"Could not measure input level: {error}")

    if outputs:
        selected_output = select_output_device(config.output_device_hint, sd_module=sd).name

    return DiagnosticsReport(
        backend_available=True,
        error=None,
        input_device_count=len(inputs),
        output_device_count=len(outputs),
        selected_input=selected_input,
        selected_output=selected_output,
        input_peak_level=peak_level,
        warnings=warnings,
    )


def _print_report(report: DiagnosticsReport) -> None:
    print("VictoriaOS Voice Node - Audio Diagnostics")
    print("=" * 44)
    for key, value in asdict(report).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    started = time.monotonic()
    result = run_diagnostics()
    _print_report(result)
    logger.info("Diagnostics completed in %.2fs", time.monotonic() - started)
