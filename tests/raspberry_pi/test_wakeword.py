from raspberry_pi.config import PiConfig
from raspberry_pi.wakeword.factory import create_wakeword_engine
from raspberry_pi.wakeword.null_engine import NullWakeWordEngine


def test_factory_falls_back_to_null_engine_without_model_path():
    config = PiConfig(wake_word_model_path="")
    engine = create_wakeword_engine(config)

    assert isinstance(engine, NullWakeWordEngine)
    assert engine.is_ready is False
    assert engine.process(b"\x00\x00") == 0.0


def test_factory_falls_back_to_null_engine_for_missing_model_file(tmp_path):
    config = PiConfig(wake_word_model_path=str(tmp_path / "does-not-exist.onnx"))
    engine = create_wakeword_engine(config)

    assert isinstance(engine, NullWakeWordEngine)


def test_null_engine_reset_is_a_safe_noop():
    engine = NullWakeWordEngine()
    engine.reset()  # should not raise
