"""openWakeWord-backed wake-word engine.

openWakeWord (https://github.com/dscripka/openWakeWord) is a real,
open-source streaming wake-word framework - not a mock. What it does *not*
ship out of the box is a model trained on "Hello Victoria"; its bundled
pretrained models are generic phrases like "hey jarvis" or "alexa". Training
a custom model needs real recorded samples of Dr. Opara (and ideally other
voices as negatives) run through openWakeWord's training pipeline, which is
a one-time manual step documented in ``docs/VOICE_PIPELINE.md`` - not
something to fake here.

So: this engine is fully wired up and will detect the wake word the moment
a trained model file is dropped at ``WAKE_WORD_MODEL_PATH`` (see
``raspberry_pi/config.py``). Until then, ``is_ready`` is ``False`` and the
wake-word service degrades gracefully (see ``service.py``) instead of
either crashing or pretending to detect a phrase it was never trained on.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from raspberry_pi.logging_config import get_logger
from raspberry_pi.wakeword.base import WakeWordEngine

logger = get_logger()


class OpenWakeWordEngine(WakeWordEngine):
    """Wake-word detection backed by a custom-trained openWakeWord model."""

    def __init__(self, model_path: str, threshold: float = 0.5) -> None:
        self.model_path = model_path
        self.threshold = threshold
        self._model = None
        self._model_key: str | None = None

        if not model_path:
            logger.warning(
                "No WAKE_WORD_MODEL_PATH configured - wake-word detection is "
                "disabled until a trained model is provided. See "
                "docs/VOICE_PIPELINE.md for how to train one."
            )
            return

        if not Path(model_path).exists():
            logger.warning(
                "Wake-word model not found at %s - wake-word detection is disabled.",
                model_path,
            )
            return

        try:
            from openwakeword.model import Model
        except ImportError:
            logger.warning(
                "openwakeword is not installed - wake-word detection is disabled. "
                "Install it with: pip install openwakeword"
            )
            return

        try:
            self._model = Model(wakeword_models=[model_path], inference_framework="onnx")
            self._model_key = Path(model_path).stem
            logger.info("Loaded wake-word model: %s", model_path)
        except Exception:
            logger.exception("Failed to load wake-word model at %s", model_path)
            self._model = None

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    def process(self, pcm_frame: bytes) -> float:
        if self._model is None:
            return 0.0

        samples = np.frombuffer(pcm_frame, dtype=np.int16)
        predictions = self._model.predict(samples)
        return float(predictions.get(self._model_key, 0.0))

    def reset(self) -> None:
        if self._model is not None:
            self._model.reset()

    def detected(self, pcm_frame: bytes) -> bool:
        """Convenience wrapper: score a frame and apply the threshold."""
        return self.process(pcm_frame) >= self.threshold
