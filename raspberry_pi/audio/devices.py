"""Audio device discovery and selection.

Never hardcodes a device index — PortAudio device indices are unstable
across reboots and USB re-enumeration (this is exactly what bit early
prototypes: a hardcoded ReSpeaker index that shifted after a firmware
update). Every lookup here goes through ``sounddevice.query_devices()`` at
call time and selects by name/capability instead.
"""

from __future__ import annotations

from dataclasses import dataclass

from raspberry_pi.logging_config import get_logger

logger = get_logger()


class AudioBackendUnavailable(RuntimeError):
    """Raised when the ``sounddevice``/PortAudio backend cannot be used."""


@dataclass(frozen=True, slots=True)
class AudioDevice:
    """A normalized view of a PortAudio device."""

    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_samplerate: float
    host_api: str

    @property
    def is_input(self) -> bool:
        return self.max_input_channels > 0

    @property
    def is_output(self) -> bool:
        return self.max_output_channels > 0


def get_sounddevice_backend():
    """Import ``sounddevice`` lazily so this module can be imported (and
    unit tested with a fake backend) even where PortAudio isn't installed.
    """
    try:
        import sounddevice as sd
    except OSError as error:  # PortAudio library missing at the OS level
        raise AudioBackendUnavailable(
            "PortAudio is not available on this system. On Raspberry Pi OS, "
            "install it with: sudo apt install libportaudio2"
        ) from error
    except ImportError as error:
        raise AudioBackendUnavailable(
            "The 'sounddevice' package is not installed. "
            "Install it with: pip install sounddevice"
        ) from error

    return sd


def list_devices(sd_module=None) -> list[AudioDevice]:
    """Return every audio device PortAudio currently knows about."""
    sd = sd_module or get_sounddevice_backend()
    host_apis = sd.query_hostapis()

    devices = []
    for index, info in enumerate(sd.query_devices()):
        devices.append(
            AudioDevice(
                index=index,
                name=info["name"],
                max_input_channels=info["max_input_channels"],
                max_output_channels=info["max_output_channels"],
                default_samplerate=info["default_samplerate"],
                host_api=host_apis[info["hostapi"]]["name"],
            )
        )

    return devices


def list_input_devices(sd_module=None) -> list[AudioDevice]:
    """Return every device that supports audio input."""
    return [device for device in list_devices(sd_module) if device.is_input]


def list_output_devices(sd_module=None) -> list[AudioDevice]:
    """Return every device that supports audio output."""
    return [device for device in list_devices(sd_module) if device.is_output]


def _matches_hint(device: AudioDevice, hint: str) -> bool:
    keywords = [keyword.strip().lower() for keyword in hint.split(",") if keyword.strip()]
    name = device.name.lower()
    return any(keyword in name for keyword in keywords)


def select_input_device(name_hint: str = "", sd_module=None) -> AudioDevice:
    """Select the best-matching input device.

    Preference order: a device whose name matches ``name_hint`` (comma
    separated keywords, e.g. ``"respeaker,seeed,usb"``), otherwise the
    system default input device, otherwise the first available input
    device. Raises if no input device exists at all.
    """
    sd = sd_module or get_sounddevice_backend()
    inputs = list_input_devices(sd)
    if not inputs:
        raise AudioBackendUnavailable("No audio input devices were found.")

    if name_hint:
        for device in inputs:
            if _matches_hint(device, name_hint):
                logger.info("Selected input device by name hint: %s", device.name)
                return device
        logger.warning(
            "No input device matched hint %r; falling back to the system default.", name_hint
        )

    try:
        default_index = sd.default.device[0]
        if default_index is not None and default_index >= 0:
            for device in inputs:
                if device.index == default_index:
                    logger.info("Selected default input device: %s", device.name)
                    return device
    except (AttributeError, TypeError, IndexError):
        pass

    logger.info("Falling back to first available input device: %s", inputs[0].name)
    return inputs[0]


def select_output_device(name_hint: str = "", sd_module=None) -> AudioDevice:
    """Select the best-matching output device (same strategy as input)."""
    sd = sd_module or get_sounddevice_backend()
    outputs = list_output_devices(sd)
    if not outputs:
        raise AudioBackendUnavailable("No audio output devices were found.")

    if name_hint:
        for device in outputs:
            if _matches_hint(device, name_hint):
                logger.info("Selected output device by name hint: %s", device.name)
                return device
        logger.warning(
            "No output device matched hint %r; falling back to the system default.", name_hint
        )

    try:
        default_index = sd.default.device[1]
        if default_index is not None and default_index >= 0:
            for device in outputs:
                if device.index == default_index:
                    logger.info("Selected default output device: %s", device.name)
                    return device
    except (AttributeError, TypeError, IndexError):
        pass

    logger.info("Falling back to first available output device: %s", outputs[0].name)
    return outputs[0]
