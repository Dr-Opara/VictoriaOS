from __future__ import annotations

import io
import wave

# Matches the format advertised to voice nodes by GET /voice/connect.
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DEFAULT_SAMPLE_WIDTH_BYTES = 2

# Below this many raw PCM bytes there isn't enough audio to plausibly
# contain speech (well under 100ms at the default format) - transcribing it
# anyway just wastes an OpenAI call and reliably returns an empty/garbage
# result, so callers should treat it as silence instead.
MIN_PCM_BYTES = 3200  # ~100ms at 16kHz/mono/16-bit


def pcm_to_wav(
    pcm: bytes,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    channels: int = DEFAULT_CHANNELS,
    sample_width: int = DEFAULT_SAMPLE_WIDTH_BYTES,
) -> bytes:
    """Wrap raw headerless PCM (as streamed by voice nodes) in a WAV container.

    Whisper (and every other STT API) needs a real audio file - a valid
    header, not just raw samples - so streamed PCM from ``/voice/stream``
    must be wrapped before it reaches :class:`SpeechService`. Uploaded files
    from ``/voice/command`` already have a real container and skip this.
    """
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm)

    return buffer.getvalue()


def is_plausible_speech_length(pcm: bytes, minimum_bytes: int = MIN_PCM_BYTES) -> bool:
    """Return False for PCM clips too short to plausibly contain speech."""
    return len(pcm) >= minimum_bytes
