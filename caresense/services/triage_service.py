"""Symptom triage service layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from functools import lru_cache

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
    },
    "Medium Urgency": {
        "care_type": "Coordinate with a primary care provider or specialist.",
        "specialty": "Internal Medicine",
        "next_steps": "Book an appointment within 24-48 hours; prepare symptom timeline.",
    },
    "High Urgency": {
        "care_type": "Seek immediate in-person care.",
        "specialty": "Emergency Medicine",
        "next_steps": "Dial emergency services or visit the ER; do not wait for virtual follow-up.",
    },
}


@dataclass
class TriageResult:
    urgency: str
    confidence: float
    enrichment: Dict[str, str]
    audit_reference: str | None


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

        audit_payload = {
            "event": "triage_completed",
            "urgency": urgency,
            "confidence": confidence,
            "biometric_reference": biometric_token,
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
        )


@lru_cache
def get_triage_service() -> TriageService:
    return TriageService()
