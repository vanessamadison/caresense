"""Pydantic models for document processing endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response after document upload and parsing."""

    file_hash: str = Field(..., description="SHA256 hash of file")
    text: str = Field(..., description="Extracted text content")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    pii_detected: Dict[str, bool] = Field(..., description="PII detection results")
    text_length: int = Field(..., description="Length of extracted text")
    warnings: Optional[list[str]] = Field(None, description="Any warnings during processing")


class DocumentTriageRequest(BaseModel):
    """Request for triage after document upload."""

    file_hash: str = Field(..., description="Hash from document upload")
    text: str = Field(..., min_length=10, description="Extracted text to triage")
    biometric_token: Optional[str] = Field(None, description="Optional biometric token")
