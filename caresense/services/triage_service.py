"""Symptom triage service layer."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from typing import Dict
from datetime import datetime, timezone

from caresense import __version__
from caresense.config import get_settings
from caresense.models.predictor import get_predictor
from caresense.utils.logging import get_logger
from caresense.workflows.compliance import ComplianceTrail

log = get_logger(__name__)

URGENCY_MAP = {
    0: "Low Urgency",
    1: "Medium Urgency",
    2: "High Urgency",
}

URGENCY_ENRICHMENT = {
    "Low Urgency": {
        "care_type": "Rest, hydration, over-the-counter support.",
        "specialty": "General Practice",
        "next_steps": "Monitor symptoms and reassess if they persist beyond 48 hours.",
        "care_window": "Self-monitor over the next 24 to 48 hours.",
        "summary": "Symptoms appear stable enough for home monitoring with routine follow-up.",
    },
    "Medium Urgency": {
        "care_type": "Coordinate with a primary care provider or specialist.",
        "specialty": "Internal Medicine",
        "next_steps": "Book an appointment within 24-48 hours; prepare symptom timeline.",
        "care_window": "Arrange clinician follow-up within 24 hours.",
        "summary": "A clinician should review this shortly to prevent avoidable deterioration.",
    },
    "High Urgency": {
        "care_type": "Seek immediate in-person care.",
        "specialty": "Emergency Medicine",
        "next_steps": "Dial emergency services or visit the ER; do not wait for virtual follow-up.",
        "care_window": "Immediate in-person assessment recommended now.",
        "summary": "Pattern indicates elevated risk and requires urgent in-person escalation.",
    },
}


@dataclass
class TriageResult:
    urgency: str
    confidence: float
    enrichment: Dict[str, str]
    audit_reference: str | None
    generated_at: str
    confidence_band: str
    probability_breakdown: Dict[str, float]
    summary: str
    symptoms_hash: str
    review_recommended: bool
    model_version: str


class TriageService:
    """Core service coordinating prediction, logging, and encryption."""

    def __init__(self) -> None:
        self._predictor = get_predictor()
        self._compliance = ComplianceTrail()
        self._settings = get_settings()

    def run_triage(self, text: str, biometric_token: str | None = None) -> TriageResult:
        prediction = self._predictor.predict_proba(text)
        index = prediction["prediction_index"]
        urgency = URGENCY_MAP.get(index, "Medium Urgency")
        confidence = float(prediction["probabilities"][index])
        enrichment = URGENCY_ENRICHMENT[urgency]
        probability_breakdown = {
            URGENCY_MAP[label_index]: round(float(score), 4)
            for label_index, score in enumerate(prediction["probabilities"])
            if label_index in URGENCY_MAP
        }
        generated_at = datetime.now(timezone.utc).isoformat()
        symptoms_hash = sha256(text.strip().lower().encode("utf-8")).hexdigest()
        confidence_band = self._confidence_band(confidence)
        review_recommended = urgency == "High Urgency" or confidence < 0.68
        summary = enrichment["summary"]

        audit_payload = {
            "event": "triage_completed",
            "urgency": urgency,
            "confidence": confidence,
            "biometric_reference": biometric_token,
            "review_recommended": review_recommended,
            "symptoms_hash": symptoms_hash,
        }
        audit_signature = self._compliance.log_event(audit_payload)

        log.info(
            "triage_result",
            urgency=urgency,
            confidence=confidence,
            has_biometric=bool(biometric_token),
            audit_signature=audit_signature,
        )

        return TriageResult(
            urgency=urgency,
            confidence=confidence,
            enrichment=enrichment,
            audit_reference=audit_signature,
            generated_at=generated_at,
            confidence_band=confidence_band,
            probability_breakdown=probability_breakdown,
            summary=summary,
            symptoms_hash=symptoms_hash,
            review_recommended=review_recommended,
            model_version=__version__,
        )

    def _confidence_band(self, confidence: float) -> str:
        if confidence >= 0.85:
            return "High confidence"
        if confidence >= 0.7:
            return "Moderate confidence"
        return "Needs clinician confirmation"


@lru_cache
def get_triage_service() -> TriageService:
    return TriageService()
