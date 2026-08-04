import numpy as np

from backend.voice.vad import VoiceActivityDetector
from backend.voice.wakeword import WakeWordDetector


def test_silence_is_not_speech():
    vad = VoiceActivityDetector()
    silence = np.zeros(16000, dtype=np.int16).tobytes()
    assert vad.is_speech(silence) is False


def test_loud_audio_is_speech():
    vad = VoiceActivityDetector()
    rng = np.random.default_rng(42)
    loud = rng.integers(-20000, 20000, 16000, dtype=np.int16).tobytes()
    assert vad.is_speech(loud) is True


def test_wake_word_detection_and_strip():
    detector = WakeWordDetector()
    assert detector.detect("Hello Victoria, what's on my calendar?") is True
    assert detector.detect("just talking to myself") is False

    remainder = detector.strip_wake_word("Hello Victoria, what's on my calendar?")
    assert remainder == "what's on my calendar?"
