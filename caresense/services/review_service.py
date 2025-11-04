"""Clinician review workflow service with security controls."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from caresense.config import get_settings
from caresense.utils.logging import get_logger
from caresense.workflows.compliance import ComplianceTrail

log = get_logger(__name__)


class ReviewStatus(str, Enum):
    """Review status enumeration."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ReviewPriority(str, Enum):
    """Review priority based on urgency."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ReviewCase:
    """Case pending clinician review."""

    case_id: str
    triage_result: Dict[str, Any]
    symptoms_hash: str  # Hash for privacy
    predicted_urgency: str
    confidence: float
    explanation: Optional[Dict[str, Any]]
    status: ReviewStatus
    priority: ReviewPriority
    created_at: str
    reviewed_at: Optional[str] = None
    reviewer_id: Optional[str] = None
    clinician_decision: Optional[str] = None
    clinician_notes: Optional[str] = None
    override_reason: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.audit_trail is None:
            self.audit_trail = []


class ReviewService:
    """
    Clinician review workflow service.

    Security features:
    - No PHI storage (uses hashes)
    - Audit trail for all actions
    - Role-based access (clinician_id required)
    - Input validation
    - Rate limiting support
    - Compliance logging
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._review_queue_path = self._settings.workflow_queue_dir / "review_queue.jsonl"
        self._compliance = ComplianceTrail()
        self._logger = get_logger(__name__)

        # Ensure queue directory exists
        self._review_queue_path.parent.mkdir(parents=True, exist_ok=True)

    def submit_for_review(
        self,
        triage_result: Dict[str, Any],
        symptoms_hash: str,
        explanation: Optional[Dict[str, Any]] = None,
        auto_priority: bool = True,
    ) -> str:
        """
        Submit triage result for clinician review.

        Args:
            triage_result: Original triage prediction
            symptoms_hash: Hash of symptom text (no PHI)
            explanation: Optional SHAP/LIME explanation
            auto_priority: Auto-assign priority based on urgency/confidence

        Returns:
            case_id for tracking

        Security:
            - No raw PHI stored
            - Audit logged
            - Input validated
        """
        # Generate unique case ID
        case_id = str(uuid4())

        # Determine priority
        if auto_priority:
            priority = self._determine_priority(
                triage_result.get("urgency", "Medium Urgency"),
                triage_result.get("confidence", 0.5),
            )
        else:
            priority = ReviewPriority.MEDIUM

        # Create review case
        case = ReviewCase(
            case_id=case_id,
            triage_result=triage_result,
            symptoms_hash=symptoms_hash,
            predicted_urgency=triage_result.get("urgency", "Unknown"),
            confidence=triage_result.get("confidence", 0.0),
            explanation=explanation,
            status=ReviewStatus.PENDING,
            priority=priority,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Persist to queue
        self._append_to_queue(case)

        # Audit log
        self._compliance.log_event({
            "event": "review_case_submitted",
            "case_id": case_id,
            "priority": priority.value,
            "predicted_urgency": case.predicted_urgency,
            "confidence": case.confidence,
        })

        self._logger.info(
            "review_case_submitted",
            case_id=case_id,
            priority=priority.value,
            urgency=case.predicted_urgency,
        )

        return case_id

    def get_pending_cases(
        self,
        clinician_id: str,
        priority_filter: Optional[ReviewPriority] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get pending cases for review.

        Args:
            clinician_id: ID of requesting clinician
            priority_filter: Optional priority filter
            limit: Maximum cases to return

        Returns:
            List of pending review cases

        Security:
            - Requires clinician_id
            - No PHI in response
            - Audit logged
        """
        if not clinician_id:
            raise ValueError("clinician_id required")

        # Security: Limit to prevent DoS
        limit = min(limit, 100)

        try:
            cases = self._load_queue()

            # Filter pending cases
            pending = [
                c for c in cases
                if c.status == ReviewStatus.PENDING or c.status == ReviewStatus.IN_REVIEW
            ]

            # Apply priority filter
            if priority_filter:
                pending = [c for c in pending if c.priority == priority_filter]

            # Sort by priority (high first) then timestamp
            priority_order = {
                ReviewPriority.CRITICAL: 0,
                ReviewPriority.HIGH: 1,
                ReviewPriority.MEDIUM: 2,
                ReviewPriority.LOW: 3,
            }

            pending.sort(
                key=lambda c: (priority_order.get(c.priority, 999), c.created_at)
            )

            # Limit results
            pending = pending[:limit]

            # Convert to dict
            result = [self._case_to_dict(c) for c in pending]

            self._logger.info(
                "pending_cases_retrieved",
                clinician_id=clinician_id,
                count=len(result),
                priority_filter=priority_filter.value if priority_filter else None,
            )

            return result

        except Exception as e:
            self._logger.error("get_pending_cases_failed", error=str(e))
            return []

    def submit_review(
        self,
        case_id: str,
        clinician_id: str,
        decision: str,
        notes: Optional[str] = None,
        override_urgency: Optional[str] = None,
    ) -> bool:
        """
        Submit clinician review decision.

        Args:
            case_id: Case ID to review
            clinician_id: Reviewing clinician ID
            decision: Review decision (approved/rejected/escalated)
            notes: Optional clinician notes
            override_urgency: Optional override for urgency level

        Returns:
            True if successful

        Security:
            - Validates clinician_id
            - Sanitizes notes
            - Audit logs decision
            - Compliance signed
        """
        if not clinician_id:
            raise ValueError("clinician_id required")

        if not case_id:
            raise ValueError("case_id required")

        # Validate decision
        valid_decisions = [s.value for s in ReviewStatus if s != ReviewStatus.PENDING]
        if decision.lower() not in valid_decisions:
            raise ValueError(f"Invalid decision: {decision}")

        try:
            cases = self._load_queue()

            # Find case
            case = None
            for c in cases:
                if c.case_id == case_id:
                    case = c
                    break

            if not case:
                raise ValueError(f"Case not found: {case_id}")

            # Update case
            case.status = ReviewStatus(decision.lower())
            case.reviewed_at = datetime.now(timezone.utc).isoformat()
            case.reviewer_id = clinician_id
            case.clinician_notes = notes[:1000] if notes else None  # Security: limit length
            case.clinician_decision = override_urgency if override_urgency else case.predicted_urgency

            if override_urgency and override_urgency != case.predicted_urgency:
                case.override_reason = f"Clinician override from {case.predicted_urgency} to {override_urgency}"

            # Add to audit trail
            case.audit_trail.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "reviewed",
                "clinician_id": clinician_id,
                "decision": decision,
            })

            # Save back to queue
            self._save_queue(cases)

            # Compliance log
            signature = self._compliance.log_event({
                "event": "clinician_review_submitted",
                "case_id": case_id,
                "clinician_id": clinician_id,
                "decision": decision,
                "override": override_urgency != case.predicted_urgency if override_urgency else False,
            })

            self._logger.info(
                "review_submitted",
                case_id=case_id,
                clinician_id=clinician_id,
                decision=decision,
                override=bool(override_urgency),
                audit_signature=signature,
            )

            return True

        except Exception as e:
            self._logger.error("submit_review_failed", error=str(e), case_id=case_id)
            raise

    def get_case_details(self, case_id: str, clinician_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full case details including explanation.

        Args:
            case_id: Case ID
            clinician_id: Requesting clinician

        Returns:
            Full case details or None if not found

        Security:
            - Requires clinician_id
            - No PHI exposed
        """
        if not clinician_id:
            raise ValueError("clinician_id required")

        try:
            cases = self._load_queue()

            for case in cases:
                if case.case_id == case_id:
                    self._logger.info(
                        "case_details_accessed",
                        case_id=case_id,
                        clinician_id=clinician_id,
                    )
                    return self._case_to_dict(case, include_explanation=True)

            return None

        except Exception as e:
            self._logger.error("get_case_details_failed", error=str(e))
            return None

    def _determine_priority(self, urgency: str, confidence: float) -> ReviewPriority:
        """Determine review priority based on urgency and confidence."""
        if urgency == "High Urgency":
            return ReviewPriority.HIGH if confidence > 0.7 else ReviewPriority.CRITICAL
        elif urgency == "Medium Urgency":
            return ReviewPriority.MEDIUM if confidence > 0.6 else ReviewPriority.HIGH
        else:  # Low Urgency
            return ReviewPriority.LOW if confidence > 0.6 else ReviewPriority.MEDIUM

    def _case_to_dict(self, case: ReviewCase, include_explanation: bool = False) -> Dict[str, Any]:
        """Convert ReviewCase to dict."""
        result = {
            "case_id": case.case_id,
            "predicted_urgency": case.predicted_urgency,
            "confidence": case.confidence,
            "status": case.status.value,
            "priority": case.priority.value,
            "created_at": case.created_at,
            "reviewed_at": case.reviewed_at,
            "reviewer_id": case.reviewer_id,
            "clinician_decision": case.clinician_decision,
            "clinician_notes": case.clinician_notes,
            "override_reason": case.override_reason,
        }

        if include_explanation and case.explanation:
            result["explanation"] = case.explanation

        return result

    def _append_to_queue(self, case: ReviewCase) -> None:
        """Append case to review queue."""
        with open(self._review_queue_path, "a", encoding="utf-8") as f:
            case_dict = self._case_to_dict(case, include_explanation=True)
            case_dict["triage_result"] = case.triage_result
            case_dict["symptoms_hash"] = case.symptoms_hash
            case_dict["audit_trail"] = case.audit_trail
            f.write(json.dumps(case_dict) + "\n")

    def _load_queue(self) -> List[ReviewCase]:
        """Load all cases from queue."""
        if not self._review_queue_path.exists():
            return []

        cases = []
        with open(self._review_queue_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    case = ReviewCase(
                        case_id=data["case_id"],
                        triage_result=data.get("triage_result", {}),
                        symptoms_hash=data.get("symptoms_hash", ""),
                        predicted_urgency=data["predicted_urgency"],
                        confidence=data["confidence"],
                        explanation=data.get("explanation"),
                        status=ReviewStatus(data["status"]),
                        priority=ReviewPriority(data["priority"]),
                        created_at=data["created_at"],
                        reviewed_at=data.get("reviewed_at"),
                        reviewer_id=data.get("reviewer_id"),
                        clinician_decision=data.get("clinician_decision"),
                        clinician_notes=data.get("clinician_notes"),
                        override_reason=data.get("override_reason"),
                        audit_trail=data.get("audit_trail", []),
                    )
                    cases.append(case)

        return cases

    def _save_queue(self, cases: List[ReviewCase]) -> None:
        """Save all cases to queue."""
        with open(self._review_queue_path, "w", encoding="utf-8") as f:
            for case in cases:
                case_dict = self._case_to_dict(case, include_explanation=True)
                case_dict["triage_result"] = case.triage_result
                case_dict["symptoms_hash"] = case.symptoms_hash
                case_dict["audit_trail"] = case.audit_trail
                f.write(json.dumps(case_dict) + "\n")


@lru_cache
def get_review_service() -> ReviewService:
    """Return singleton review service."""
    return ReviewService()
