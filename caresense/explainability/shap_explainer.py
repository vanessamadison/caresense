"""SHAP-based model explainability with security controls."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any, Dict, List

import numpy as np
import shap
from sklearn.pipeline import Pipeline

from caresense.config import get_settings
from caresense.models.predictor import get_predictor
from caresense.utils.logging import get_logger

log = get_logger(__name__)

# Security: Limit explanation complexity to prevent DoS
MAX_SAMPLES_FOR_EXPLANATION = 100
MAX_FEATURES_TO_EXPLAIN = 20
FEATURE_TRUNCATE_LENGTH = 50


class SHAPExplainer:
    """
    SHAP-based explainer with security hardening.

    Security measures:
    - Input length validation to prevent DoS
    - Feature truncation to prevent memory exhaustion
    - Sample size limits for computational safety
    - Audit logging of all explanations generated
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._predictor = get_predictor()
        self._explainer: shap.Explainer | None = None
        self._background_data: np.ndarray | None = None

    def _get_pipeline(self) -> Pipeline:
        """Load the trained pipeline."""
        return self._predictor.load()

    def _initialize_explainer(self) -> None:
        """
        Initialize SHAP explainer with background data.

        Security: Uses limited background samples to prevent memory issues.
        """
        if self._explainer is not None:
            return

        pipeline = self._get_pipeline()

        # Security: Use small background dataset
        try:
            # Create synthetic background data for initialization
            background_texts = [
                "fever headache cough",
                "chest pain shortness of breath",
                "nausea vomiting diarrhea",
                "joint pain swelling",
                "rash itching",
            ]

            # Transform through the pipeline up to the classifier
            vectorizer = pipeline.named_steps["tfidf"]
            svd = pipeline.named_steps["svd"]

            background_vectors = vectorizer.transform(background_texts)
            background_reduced = svd.transform(background_vectors)

            self._background_data = background_reduced

            # Use KernelExplainer for model-agnostic explanations
            classifier = pipeline.named_steps["clf"]
            self._explainer = shap.KernelExplainer(
                classifier.predict_proba,
                self._background_data,
                link="logit",
            )

            log.info("shap_explainer_initialized", background_samples=len(background_texts))

        except Exception as e:
            log.error("shap_initialization_failed", error=str(e))
            raise

    def explain(self, text: str, audit: bool = True) -> Dict[str, Any]:
        """
        Generate SHAP explanation for a prediction.

        Args:
            text: Input text to explain
            audit: Whether to log this explanation request

        Returns:
            Dict containing:
                - top_features: List of (feature, importance) tuples
                - shap_values: Raw SHAP values
                - base_value: Model base value
                - request_hash: Hash of input for audit trail

        Security:
            - Validates input length
            - Limits computation complexity
            - Sanitizes feature names
            - Logs explanation requests
        """
        # Security: Validate input length
        if len(text) > 10000:
            log.warning("shap_input_too_long", length=len(text))
            raise ValueError("Input text exceeds maximum length for explanation")

        if len(text.strip()) == 0:
            raise ValueError("Empty input text")

        # Security: Hash input for audit trail (no PII in logs)
        request_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

        try:
            self._initialize_explainer()

            pipeline = self._get_pipeline()
            vectorizer = pipeline.named_steps["tfidf"]
            svd = pipeline.named_steps["svd"]

            # Transform input through pipeline
            text_vector = vectorizer.transform([text])
            text_reduced = svd.transform(text_vector)

            # Security: Limit SHAP computation samples
            shap_values = self._explainer.shap_values(
                text_reduced,
                nsamples=min(MAX_SAMPLES_FOR_EXPLANATION, 100),
            )

            # Get feature names from TF-IDF (before SVD reduction)
            feature_names = vectorizer.get_feature_names_out()
            text_features = text_vector.toarray()[0]

            # Map SVD components back to original features
            # Get top contributing original features
            svd_components = svd.components_  # shape: (n_components, n_features)

            # For the predicted class, get SHAP values
            predicted_class = np.argmax(shap_values[0]) if isinstance(shap_values, list) else 0
            class_shap_values = shap_values[predicted_class] if isinstance(shap_values, list) else shap_values

            # Compute feature importance: SVD component * SHAP value
            feature_importance = np.zeros(len(feature_names))
            for i, shap_val in enumerate(class_shap_values[0]):
                feature_importance += svd_components[i] * shap_val

            # Get top features
            top_indices = np.argsort(np.abs(feature_importance))[-MAX_FEATURES_TO_EXPLAIN:][::-1]

            # Security: Sanitize feature names (truncate, remove potential injection)
            top_features = []
            for idx in top_indices:
                if text_features[idx] > 0:  # Only include features present in input
                    feature_name = str(feature_names[idx])[:FEATURE_TRUNCATE_LENGTH]
                    # Remove special characters that might cause issues
                    feature_name = "".join(c for c in feature_name if c.isalnum() or c in [" ", "_", "-"])
                    importance = float(feature_importance[idx])
                    top_features.append({
                        "feature": feature_name,
                        "importance": round(importance, 6),
                    })

            # Limit to top 10 for response size
            top_features = top_features[:10]

            result = {
                "top_features": top_features,
                "base_value": float(self._explainer.expected_value[predicted_class]) if isinstance(
                    self._explainer.expected_value, (list, np.ndarray)
                ) else float(self._explainer.expected_value),
                "predicted_class": int(predicted_class),
                "request_hash": request_hash,
                "explanation_method": "shap_kernel",
            }

            if audit:
                log.info(
                    "shap_explanation_generated",
                    request_hash=request_hash,
                    num_features=len(top_features),
                    predicted_class=predicted_class,
                )

            return result

        except Exception as e:
            log.error("shap_explanation_failed", error=str(e), request_hash=request_hash)
            raise

    def get_global_feature_importance(self) -> List[Dict[str, Any]]:
        """
        Get global feature importance across the model.

        Returns:
            List of features with importance scores

        Security: Limited to prevent resource exhaustion
        """
        try:
            pipeline = self._get_pipeline()
            classifier = pipeline.named_steps["clf"]

            # For logistic regression, we can get coefficients
            if hasattr(classifier, "calibrated_classifiers_"):
                # CalibratedClassifierCV wrapper
                base_clf = classifier.calibrated_classifiers_[0].estimator
                if hasattr(base_clf, "coef_"):
                    coef = base_clf.coef_[0]

                    # Get feature names from SVD space
                    svd = pipeline.named_steps["svd"]
                    n_components = svd.n_components

                    global_importance = []
                    for i in range(min(n_components, MAX_FEATURES_TO_EXPLAIN)):
                        global_importance.append({
                            "component": f"svd_component_{i}",
                            "importance": float(abs(coef[i])),
                        })

                    global_importance.sort(key=lambda x: x["importance"], reverse=True)

                    log.info("global_importance_computed", num_features=len(global_importance))
                    return global_importance[:10]

            return []

        except Exception as e:
            log.error("global_importance_failed", error=str(e))
            return []


@lru_cache
def get_shap_explainer() -> SHAPExplainer:
    """Return singleton SHAP explainer instance."""
    return SHAPExplainer()
