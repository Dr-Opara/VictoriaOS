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
    ambient_noise_rms: float | None
    recommended_vad_threshold: int | None
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


def calibrate_noise_floor(
    device_index: int,
    sample_rate: int = 16000,
    duration_seconds: float = 2.0,
    sd_module=None,
) -> tuple[float, int]:
    """Record ambient (room) noise and recommend a VAD energy threshold.

    Returns ``(ambient_rms, recommended_threshold)``. The recommendation is
    the ambient RMS with a safety margin, clamped to a sane range - it's a
    starting point for ``VAD_ENERGY_THRESHOLD``, not a guarantee against
    every noisy environment (see docs/VOICE_PIPELINE.md).
    """
    sd = sd_module or get_sounddevice_backend()
    recording = sd.rec(
        int(duration_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        device=device_index,
    )
    sd.wait()

    samples = recording.astype(np.float64)
    ambient_rms = float(np.sqrt(np.mean(np.square(samples))))
    recommended = int(min(max(ambient_rms * 4, 200), 4000))
    return ambient_rms, recommended


def run_diagnostics(measure_level: bool = True, calibrate_noise: bool = False) -> DiagnosticsReport:
    """Run a full audio subsystem diagnostic sweep.

    ``calibrate_noise`` additionally records a couple of seconds of ambient
    room noise and recommends a ``VAD_ENERGY_THRESHOLD`` - keep the room at
    its normal background noise level (not silent) while this runs.
    """
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
            ambient_noise_rms=None,
            recommended_vad_threshold=None,
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
    ambient_rms = None
    recommended_threshold = None

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

        if calibrate_noise:
            try:
                ambient_rms, recommended_threshold = calibrate_noise_floor(
                    device.index, sd_module=sd
                )
                if recommended_threshold >= config.vad_energy_threshold:
                    warnings.append(
                        f"Ambient noise (rms={ambient_rms:.0f}) is high relative to the "
                        f"configured VAD_ENERGY_THRESHOLD ({config.vad_energy_threshold:.0f}). "
                        f"Consider raising it to at least {recommended_threshold} to avoid "
                        "false triggers from background noise."
                    )
            except Exception as error:  # pragma: no cover - hardware dependent
                warnings.append(f"Could not calibrate noise floor: {error}")

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
        ambient_noise_rms=ambient_rms,
        recommended_vad_threshold=recommended_threshold,
        warnings=warnings,
    )


def _print_report(report: DiagnosticsReport) -> None:
    print("VictoriaOS Voice Node - Audio Diagnostics")
    print("=" * 44)
    for key, value in asdict(report).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    import sys

    calibrate = "--calibrate-noise" in sys.argv
    started = time.monotonic()
    result = run_diagnostics(calibrate_noise=calibrate)
    _print_report(result)
    logger.info("Diagnostics completed in %.2fs", time.monotonic() - started)
