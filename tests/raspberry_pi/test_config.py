from raspberry_pi.config import get_config


def test_defaults_are_sane():
    config = get_config()

    assert config.mini_pc_url == "http://localhost:8000"
    assert config.sample_rate == 16000
    assert config.wake_word_phrase == "hello victoria"
    assert config.speaker_verification_enabled is False


def test_env_overrides_are_picked_up(monkeypatch):
    monkeypatch.setenv("MINI_PC_URL", "http://10.0.0.5:9000")
    monkeypatch.setenv("SAMPLE_RATE", "48000")
    monkeypatch.setenv("SPEAKER_VERIFICATION_ENABLED", "true")

    config = get_config()

    assert config.mini_pc_url == "http://10.0.0.5:9000"
    assert config.sample_rate == 48000
    assert config.speaker_verification_enabled is True
