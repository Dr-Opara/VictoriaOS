import pytest

from raspberry_pi.audio.devices import (
    AudioBackendUnavailable,
    list_input_devices,
    list_output_devices,
    select_input_device,
    select_output_device,
)


class FakeDefault:
    device = (1, 2)


class FakeSoundDevice:
    """Minimal stand-in for the ``sounddevice`` module's device query API."""

    default = FakeDefault()

    _devices = [
        {"name": "Built-in Mic", "max_input_channels": 2, "max_output_channels": 0, "default_samplerate": 44100.0, "hostapi": 0},
        {"name": "ReSpeaker 4 Mic Array", "max_input_channels": 4, "max_output_channels": 0, "default_samplerate": 16000.0, "hostapi": 0},
        {"name": "Built-in Speaker", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 44100.0, "hostapi": 0},
        {"name": "HDMI Output", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 48000.0, "hostapi": 0},
    ]

    @classmethod
    def query_devices(cls):
        return cls._devices

    @staticmethod
    def query_hostapis():
        return [{"name": "ALSA"}]


def test_list_input_devices_filters_to_inputs_only():
    inputs = list_input_devices(FakeSoundDevice)
    assert [d.name for d in inputs] == ["Built-in Mic", "ReSpeaker 4 Mic Array"]


def test_list_output_devices_filters_to_outputs_only():
    outputs = list_output_devices(FakeSoundDevice)
    assert [d.name for d in outputs] == ["Built-in Speaker", "HDMI Output"]


def test_select_input_device_matches_name_hint_over_default():
    device = select_input_device("respeaker,seeed,usb", sd_module=FakeSoundDevice)
    assert device.name == "ReSpeaker 4 Mic Array"


def test_select_input_device_falls_back_to_default_index():
    device = select_input_device("", sd_module=FakeSoundDevice)
    assert device.index == 1
    assert device.name == "ReSpeaker 4 Mic Array"


def test_select_output_device_falls_back_to_default_index():
    device = select_output_device("", sd_module=FakeSoundDevice)
    assert device.index == 2
    assert device.name == "Built-in Speaker"


def test_select_input_device_raises_when_none_available():
    class NoInputs(FakeSoundDevice):
        _devices = [FakeSoundDevice._devices[2]]

    with pytest.raises(AudioBackendUnavailable):
        select_input_device("", sd_module=NoInputs)
