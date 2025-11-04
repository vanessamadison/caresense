"""Pydantic models for clinician review endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReviewCaseResponse(BaseModel):
    """Single review case."""

    case_id: str
    predicted_urgency: str
    confidence: float
    status: str
    priority: str
    created_at: str
    reviewed_at: Optional[str] = None
    reviewer_id: Optional[str] = None
    clinician_decision: Optional[str] = None
    clinician_notes: Optional[str] = None
    override_reason: Optional[str] = None
    explanation: Optional[Dict[str, Any]] = None


class PendingCasesResponse(BaseModel):
    """List of pending review cases."""

    cases: List[ReviewCaseResponse]
    total: int
    priority_filter: Optional[str] = None


class SubmitReviewRequest(BaseModel):
    """Clinician review submission."""

    case_id: str = Field(..., description="Case ID to review")
    clinician_id: str = Field(..., min_length=1, description="Reviewing clinician ID")
    decision: str = Field(
        ...,
        description="Decision: approved, rejected, escalated",
        pattern="^(approved|rejected|escalated|in_review)$",
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Clinician notes")
    override_urgency: Optional[str] = Field(
        None,
        description="Override urgency level",
        pattern="^(Low Urgency|Medium Urgency|High Urgency)$",
    )


class SubmitReviewResponse(BaseModel):
    """Response after review submission."""

    success: bool
    case_id: str
    audit_signature: Optional[str] = None
