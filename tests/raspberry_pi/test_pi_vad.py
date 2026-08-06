import numpy as np

from raspberry_pi.audio.vad import EndpointDetector, VoiceActivityDetector


def _silence(frame_samples: int) -> bytes:
    return np.zeros(frame_samples, dtype=np.int16).tobytes()


def _loud(frame_samples: int) -> bytes:
    rng = np.random.default_rng(7)
    return rng.integers(-20000, 20000, frame_samples, dtype=np.int16).tobytes()


def test_is_speech_distinguishes_silence_and_loud_audio():
    vad = VoiceActivityDetector(sample_rate=16000, frame_ms=30)
    frame_samples = int(16000 * 30 / 1000)

    assert vad.is_speech(_silence(frame_samples)) is False
    assert vad.is_speech(_loud(frame_samples)) is True


def test_endpoint_detector_fires_after_sustained_silence_following_speech():
    vad = VoiceActivityDetector(sample_rate=16000, frame_ms=30, silence_hold_ms=90)
    detector = EndpointDetector(vad)
    frame_samples = int(16000 * 30 / 1000)

    assert detector.push(_loud(frame_samples)) is False
    assert detector.push(_silence(frame_samples)) is False
    assert detector.push(_silence(frame_samples)) is False
    assert detector.push(_silence(frame_samples)) is True


def test_endpoint_detector_does_not_fire_on_leading_silence():
    vad = VoiceActivityDetector(sample_rate=16000, frame_ms=30, silence_hold_ms=30)
    detector = EndpointDetector(vad)
    frame_samples = int(16000 * 30 / 1000)

    for _ in range(5):
        assert detector.push(_silence(frame_samples)) is False


def test_reset_clears_state():
    vad = VoiceActivityDetector(sample_rate=16000, frame_ms=30, silence_hold_ms=30)
    detector = EndpointDetector(vad)
    frame_samples = int(16000 * 30 / 1000)

    detector.push(_loud(frame_samples))
    detector.reset()
    assert detector.push(_silence(frame_samples)) is False
