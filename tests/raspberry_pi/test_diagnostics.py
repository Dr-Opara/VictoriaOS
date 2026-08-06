import numpy as np

from raspberry_pi.audio.diagnostics import (
    AudioBackendUnavailable,
    calibrate_noise_floor,
    measure_input_level,
    run_diagnostics,
)


class FakeDefault:
    device = (0, 1)


class FakeSoundDevice:
    """Fake sounddevice backend with deterministic recorded levels."""

    default = FakeDefault()
    _recording_value = 16000  # ~49% of int16 full scale

    _devices = [
        {"name": "Test Mic", "max_input_channels": 1, "max_output_channels": 0, "default_samplerate": 16000.0, "hostapi": 0},
        {"name": "Test Speaker", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 44100.0, "hostapi": 0},
    ]

    @classmethod
    def query_devices(cls):
        return cls._devices

    @staticmethod
    def query_hostapis():
        return [{"name": "ALSA"}]

    @classmethod
    def rec(cls, frames, samplerate, channels, dtype, device):
        return np.full((frames, channels), cls._recording_value, dtype=dtype)

    @staticmethod
    def wait():
        return None


class SilentSoundDevice(FakeSoundDevice):
    _recording_value = 0


class NoDevicesSoundDevice(FakeSoundDevice):
    _devices = []


def test_measure_input_level_reflects_recorded_amplitude():
    level = measure_input_level(0, sd_module=FakeSoundDevice)
    assert 0.4 < level < 0.6


def test_measure_input_level_zero_for_silence():
    level = measure_input_level(0, sd_module=SilentSoundDevice)
    assert level == 0.0


class QuietRoomSoundDevice(FakeSoundDevice):
    _recording_value = 150  # realistic quiet-room ambient noise


def test_calibrate_noise_floor_recommends_threshold_above_ambient():
    ambient_rms, recommended = calibrate_noise_floor(0, sd_module=QuietRoomSoundDevice)
    assert ambient_rms > 0
    assert recommended > ambient_rms
    assert 200 <= recommended <= 4000


def test_calibrate_noise_floor_clamps_high_ambient_noise():
    # A loud room (e.g. near-full-scale input) should still yield a capped,
    # sane recommendation rather than an unusably high threshold.
    _, recommended = calibrate_noise_floor(0, sd_module=FakeSoundDevice)
    assert recommended == 4000


def test_run_diagnostics_reports_backend_unavailable_cleanly():
    def raise_unavailable(sd_module=None):
        raise AudioBackendUnavailable("no portaudio")

    import raspberry_pi.audio.diagnostics as diagnostics_module

    original = diagnostics_module.get_sounddevice_backend
    diagnostics_module.get_sounddevice_backend = raise_unavailable
    try:
        report = run_diagnostics()
    finally:
        diagnostics_module.get_sounddevice_backend = original

    assert report.backend_available is False
    assert report.error is not None
    assert report.warnings == []


def test_run_diagnostics_warns_when_no_devices(monkeypatch):
    import raspberry_pi.audio.diagnostics as diagnostics_module

    monkeypatch.setattr(diagnostics_module, "get_sounddevice_backend", lambda: NoDevicesSoundDevice)

    report = run_diagnostics(measure_level=False)

    assert report.backend_available is True
    assert report.input_device_count == 0
    assert report.output_device_count == 0
    assert any("input" in warning.lower() for warning in report.warnings)
    assert any("output" in warning.lower() for warning in report.warnings)


def test_run_diagnostics_full_sweep_with_calibration(monkeypatch):
    import raspberry_pi.audio.diagnostics as diagnostics_module

    monkeypatch.setattr(diagnostics_module, "get_sounddevice_backend", lambda: FakeSoundDevice)

    report = run_diagnostics(measure_level=True, calibrate_noise=True)

    assert report.backend_available is True
    assert report.selected_input == "Test Mic"
    assert report.selected_output == "Test Speaker"
    assert report.input_peak_level is not None
    assert report.ambient_noise_rms is not None
    assert report.recommended_vad_threshold is not None
