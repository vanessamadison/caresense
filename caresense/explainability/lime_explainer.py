"""LIME-based text explainability with security controls."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any, Dict, List

import lime
import lime.lime_text
from sklearn.pipeline import Pipeline

from caresense.models.predictor import get_predictor
from caresense.utils.logging import get_logger

log = get_logger(__name__)

# Security: Limit explanation complexity
MAX_NUM_FEATURES = 10
MAX_NUM_SAMPLES = 500
MAX_INPUT_LENGTH = 10000


class LIMEExplainer:
    """
    LIME-based text explainer with security hardening.

    Security measures:
    - Input validation and sanitization
    - Computational limits to prevent DoS
    - Audit logging
    - Safe HTML generation (no XSS)
    """

    def __init__(self) -> None:
        self._predictor = get_predictor()
        self._explainer: lime.lime_text.LimeTextExplainer | None = None

    def _initialize_explainer(self) -> None:
        """Initialize LIME text explainer."""
        if self._explainer is not None:
            return

        # LIME explainer for text classification
        self._explainer = lime.lime_text.LimeTextExplainer(
            class_names=["Low Urgency", "Medium Urgency", "High Urgency"],
            bow=False,  # Use original text representation
            random_state=42,
        )

        log.info("lime_explainer_initialized")

    def explain(self, text: str, audit: bool = True) -> Dict[str, Any]:
        """
        Generate LIME explanation for text classification.

        Args:
            text: Input text to explain
            audit: Whether to log explanation request

        Returns:
            Dict containing:
                - top_features: List of (word, importance) for predicted class
                - prediction_probabilities: Class probabilities
                - predicted_class: Predicted class index
                - request_hash: Input hash for audit

        Security:
            - Validates input length
            - Limits computational samples
            - Sanitizes output
            - Audit logs requests
        """
        # Security: Validate input
        if len(text) > MAX_INPUT_LENGTH:
            log.warning("lime_input_too_long", length=len(text))
            raise ValueError("Input text exceeds maximum length")

        if len(text.strip()) == 0:
            raise ValueError("Empty input text")

        # Security: Hash for audit (no PII)
        request_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

        try:
            self._initialize_explainer()

            # Get prediction function from pipeline
            pipeline = self._predictor.load()

            def predict_fn(texts: List[str]) -> Any:
                """Prediction function for LIME."""
                return pipeline.predict_proba(texts)

            # Security: Limit number of samples for LIME
            explanation = self._explainer.explain_instance(
                text,
                predict_fn,
                num_features=MAX_NUM_FEATURES,
                num_samples=MAX_NUM_SAMPLES,
            )

            # Get predicted class
            probs = predict_fn([text])[0]
            predicted_class = int(probs.argmax())

            # Get feature importance for predicted class
            feature_weights = explanation.as_list(label=predicted_class)

            # Security: Sanitize feature names
            top_features = []
            for word, weight in feature_weights:
                # Remove special chars, limit length
                sanitized_word = "".join(
                    c for c in str(word)[:50] if c.isalnum() or c in [" ", "_", "-"]
                )
                top_features.append({
                    "word": sanitized_word,
                    "importance": round(float(weight), 6),
                })

            result = {
                "top_features": top_features,
                "prediction_probabilities": {
                    "Low Urgency": round(float(probs[0]), 4),
                    "Medium Urgency": round(float(probs[1]), 4),
                    "High Urgency": round(float(probs[2]), 4),
                },
                "predicted_class": predicted_class,
                "predicted_class_name": ["Low Urgency", "Medium Urgency", "High Urgency"][predicted_class],
                "request_hash": request_hash,
                "explanation_method": "lime_text",
            }

            if audit:
                log.info(
                    "lime_explanation_generated",
                    request_hash=request_hash,
                    predicted_class=predicted_class,
                    num_features=len(top_features),
                )

            return result

        except Exception as e:
            log.error("lime_explanation_failed", error=str(e), request_hash=request_hash)
            raise


@lru_cache
def get_lime_explainer() -> LIMEExplainer:
    """Return singleton LIME explainer instance."""
    return LIMEExplainer()
