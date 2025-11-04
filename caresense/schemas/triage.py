"""Pydantic models for triage endpoints."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class BiometricEnrollmentRequest(BaseModel):
    vector: List[float] = Field(..., min_length=16, description="Normalized biometric embedding")


class BiometricEnrollmentResponse(BaseModel):
    token_id: str
    ciphertext: str


class TriageRequest(BaseModel):
    symptoms: str = Field(..., min_length=10, description="Free-text symptom description")
    biometric_token: Optional[str] = Field(
        default=None,
        description="Reference to encrypted biometric session",
    )
    biometric_vector: Optional[List[float]] = Field(
        default=None,
        description="Fresh biometric embedding for zero-knowledge revalidation",
    )


class TriageResponse(BaseModel):
    urgency: str
    confidence: float
    recommended_care: str
    specialty: str
    next_steps: str
    audit_reference: str | None = None


class CompliancePublicKeyResponse(BaseModel):
    algorithm: str = Field(default="ed25519")
    public_key_pem: str
