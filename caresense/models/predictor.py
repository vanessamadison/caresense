"""Triage model loading and inference utilities."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import joblib

from caresense.config import get_settings
from caresense.utils.logging import get_logger

log = get_logger(__name__)


class Predictor:
    """Wrapper around the triage ML pipeline."""

    def __init__(self) -> None:
        settings = get_settings()
        self._model_path = settings.model_path
        self._pipeline = None

    def load(self) -> Any:
        if self._pipeline is None:
            log.info("model_loading", path=str(self._model_path))
            self._pipeline = joblib.load(self._model_path)
        return self._pipeline

    def predict_proba(self, text: str) -> dict[str, Any]:
        pipeline = self.load()
        probabilities = pipeline.predict_proba([text])[0]
        prediction = probabilities.argmax()

        return {
            "prediction_index": int(prediction),
            "probabilities": probabilities.tolist(),
        }


@lru_cache
def get_predictor() -> Predictor:
    return Predictor()
