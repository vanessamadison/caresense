"""Pydantic models for explainability endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    """Request for model explanation."""

    text: str = Field(..., min_length=10, max_length=10000, description="Text to explain")
    method: str = Field(
        default="shap",
        description="Explanation method: 'shap' or 'lime'",
        pattern="^(shap|lime)$",
    )


class FeatureImportance(BaseModel):
    """Feature importance item."""

    feature: str = Field(..., description="Feature name or word")
    importance: float = Field(..., description="Importance score")


class ExplainResponse(BaseModel):
    """Response with model explanation."""

    top_features: List[FeatureImportance] = Field(..., description="Top contributing features")
    predicted_class: int = Field(..., description="Predicted class index")
    predicted_class_name: Optional[str] = Field(None, description="Predicted class name")
    prediction_probabilities: Optional[Dict[str, float]] = Field(
        None, description="Class probabilities"
    )
    base_value: Optional[float] = Field(None, description="SHAP base value")
    explanation_method: str = Field(..., description="Method used for explanation")
    request_hash: str = Field(..., description="Request hash for audit")


class GlobalImportanceResponse(BaseModel):
    """Global feature importance across model."""

    features: List[FeatureImportance] = Field(..., description="Global feature importance")
    model_type: str = Field(..., description="Model type")
