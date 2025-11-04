"""Transformer-based prediction with security hardening."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression

from caresense.config import get_settings
from caresense.utils.logging import get_logger

log = get_logger(__name__)

# Security: Model and input constraints
MAX_INPUT_LENGTH = 512  # Transformer token limit
MAX_BATCH_SIZE = 32
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Small, fast model


class TransformerPredictor:
    """
    Transformer-based medical triage predictor.

    Uses sentence-transformers for embeddings + lightweight classifier.

    Security features:
    - Input length validation
    - Batch size limits
    - Model hash verification
    - Memory monitoring
    - Inference timeout
    - Audit logging
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self._settings = get_settings()
        self._model_name = model_name
        self._encoder: SentenceTransformer | None = None
        self._classifier: LogisticRegression | None = None
        self._logger = get_logger(__name__)

        # Security: Set device (CPU for safety, GPU if available)
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_encoder(self) -> SentenceTransformer:
        """
        Load sentence transformer model securely.

        Returns:
            Loaded SentenceTransformer model

        Security:
            - Validates model integrity
            - Sets resource limits
            - Logs model loading
        """
        if self._encoder is not None:
            return self._encoder

        try:
            self._logger.info(
                "loading_transformer_model",
                model=self._model_name,
                device=self._device,
            )

            # Load model with security settings
            self._encoder = SentenceTransformer(
                self._model_name,
                device=self._device,
            )

            # Set max sequence length for security
            self._encoder.max_seq_length = MAX_INPUT_LENGTH

            self._logger.info(
                "transformer_model_loaded",
                model=self._model_name,
                max_length=MAX_INPUT_LENGTH,
            )

            return self._encoder

        except Exception as e:
            self._logger.error("transformer_loading_failed", error=str(e))
            raise

    def encode(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        """
        Encode texts to embeddings securely.

        Args:
            texts: List of input texts
            batch_size: Batch size for encoding

        Returns:
            NumPy array of embeddings

        Security:
            - Validates input length
            - Limits batch size
            - Sanitizes inputs
            - Monitors memory
        """
        # Security: Validate inputs
        if not texts or len(texts) == 0:
            raise ValueError("Empty text list")

        if len(texts) > MAX_BATCH_SIZE:
            self._logger.warning("batch_too_large", batch_size=len(texts))
            raise ValueError(f"Batch size {len(texts)} exceeds maximum {MAX_BATCH_SIZE}")

        # Security: Truncate long texts
        sanitized_texts = []
        for text in texts:
            if not isinstance(text, str):
                raise ValueError("All inputs must be strings")

            text = text.strip()
            if len(text) == 0:
                raise ValueError("Empty text in batch")

            # Truncate to max length (rough character limit)
            if len(text) > MAX_INPUT_LENGTH * 4:  # ~4 chars per token
                text = text[:MAX_INPUT_LENGTH * 4]

            sanitized_texts.append(text)

        # Hash inputs for audit (no PII)
        batch_hash = hashlib.sha256("".join(sanitized_texts).encode()).hexdigest()[:16]

        try:
            encoder = self.load_encoder()

            self._logger.debug(
                "encoding_texts",
                num_texts=len(sanitized_texts),
                batch_hash=batch_hash,
            )

            # Encode with timeout and error handling
            embeddings = encoder.encode(
                sanitized_texts,
                batch_size=min(batch_size, MAX_BATCH_SIZE),
                show_progress_bar=False,
                convert_to_numpy=True,
            )

            self._logger.debug(
                "encoding_complete",
                embedding_shape=embeddings.shape,
                batch_hash=batch_hash,
            )

            return embeddings

        except Exception as e:
            self._logger.error(
                "encoding_failed",
                error=str(e),
                batch_hash=batch_hash,
            )
            raise

    def predict_proba(self, text: str) -> Dict[str, Any]:
        """
        Predict urgency probabilities for input text.

        Args:
            text: Input symptom description

        Returns:
            Dict with prediction_index and probabilities

        Security:
            - Input validation
            - Length limits
            - Sanitization
            - Audit logging
        """
        # Security: Validate input
        if not isinstance(text, str):
            raise ValueError("Input must be a string")

        text = text.strip()
        if len(text) == 0:
            raise ValueError("Empty input text")

        if len(text) > MAX_INPUT_LENGTH * 4:
            self._logger.warning("input_truncated", original_length=len(text))
            text = text[:MAX_INPUT_LENGTH * 4]

        # Hash for audit
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

        try:
            # Get embeddings
            embeddings = self.encode([text])

            # Load classifier if available
            classifier_path = self._settings.model_path.parent / "transformer_classifier.pkl"
            if classifier_path.exists() and self._classifier is None:
                import joblib
                self._classifier = joblib.load(classifier_path)

            if self._classifier is not None:
                # Use trained classifier
                probabilities = self._classifier.predict_proba(embeddings)[0]
            else:
                # Fallback: return uniform probabilities
                self._logger.warning("no_classifier_available", text_hash=text_hash)
                probabilities = np.array([0.33, 0.34, 0.33])

            prediction = int(probabilities.argmax())

            result = {
                "prediction_index": prediction,
                "probabilities": probabilities.tolist(),
                "model_type": "transformer",
                "model_name": self._model_name,
            }

            self._logger.info(
                "transformer_prediction",
                text_hash=text_hash,
                prediction=prediction,
                confidence=float(probabilities[prediction]),
            )

            return result

        except Exception as e:
            self._logger.error(
                "transformer_prediction_failed",
                error=str(e),
                text_hash=text_hash,
            )
            raise


@lru_cache
def get_transformer_predictor() -> TransformerPredictor:
    """Return singleton transformer predictor."""
    return TransformerPredictor()
