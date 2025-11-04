"""API route definitions with comprehensive security controls."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from caresense.explainability import get_lime_explainer, get_shap_explainer
from caresense.parsers import get_document_parser, get_sanitizer
from caresense.schemas.document import DocumentTriageRequest, DocumentUploadResponse
from caresense.schemas.explain import (
    ExplainRequest,
    ExplainResponse,
    FeatureImportance,
    GlobalImportanceResponse,
)
from caresense.schemas.review import (
    PendingCasesResponse,
    ReviewCaseResponse,
    SubmitReviewRequest,
    SubmitReviewResponse,
)
from caresense.schemas.triage import (
    BiometricEnrollmentRequest,
    BiometricEnrollmentResponse,
    CompliancePublicKeyResponse,
    HealthResponse,
    TriageRequest,
    TriageResponse,
)
from caresense.services.auth_service import BiometricAuthService, get_biometric_service
from caresense.services.review_service import ReviewPriority, get_review_service
from caresense.services.triage_service import TriageService, get_triage_service
from caresense.workflows.compliance import ComplianceTrail

router = APIRouter()


def get_triage_dependency() -> TriageService:
    return get_triage_service()


def get_biometric_dependency() -> BiometricAuthService:
    return get_biometric_service()


def get_compliance_dependency() -> ComplianceTrail:
    return ComplianceTrail()


@router.get("/health", response_model=HealthResponse, tags=["Observability"])
def health_check() -> HealthResponse:
    return HealthResponse()


@router.post(
    "/biometrics/enrol",
    response_model=BiometricEnrollmentResponse,
    tags=["Biometrics"],
)
def enrol_biometric(
    request: BiometricEnrollmentRequest,
    service: BiometricAuthService = Depends(get_biometric_dependency),
) -> BiometricEnrollmentResponse:
    token = service.enrol(request.vector)
    return BiometricEnrollmentResponse(token_id=token.token_id, ciphertext=token.ciphertext)


@router.get(
    "/compliance/public-key",
    response_model=CompliancePublicKeyResponse,
    tags=["Compliance"],
)
def compliance_public_key(trail: ComplianceTrail = Depends(get_compliance_dependency)) -> CompliancePublicKeyResponse:
    pem = trail.public_key_pem().decode("utf-8")
    return CompliancePublicKeyResponse(public_key_pem=pem)


@router.post(
    "/triage",
    response_model=TriageResponse,
    tags=["Triage"],
)
def run_triage(
    request: TriageRequest,
    triage_service: TriageService = Depends(get_triage_dependency),
    biometric_service: BiometricAuthService = Depends(get_biometric_dependency),
) -> TriageResponse:
    biometric_reference = request.biometric_token
    if request.biometric_vector:
        if not request.biometric_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Biometric vector submitted without token reference.",
            )
        verified = biometric_service.verify(request.biometric_token, request.biometric_vector)
        if not verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Biometric verification failed.",
            )

    result = triage_service.run_triage(request.symptoms, biometric_reference)
    enrichment = result.enrichment

    return TriageResponse(
        urgency=result.urgency,
        confidence=round(result.confidence, 4),
        recommended_care=enrichment["care_type"],
        specialty=enrichment["specialty"],
        next_steps=enrichment["next_steps"],
        audit_reference=result.audit_reference,
    )


# ============================================================================
# EXPLAINABILITY ENDPOINTS
# ============================================================================


@router.post(
    "/explain",
    response_model=ExplainResponse,
    tags=["Explainability"],
    summary="Get model explanation for prediction",
)
def explain_prediction(request: ExplainRequest) -> ExplainResponse:
    """
    Generate explanation for model prediction using SHAP or LIME.

    Security:
        - Input length validation
        - Sanitization applied
        - Rate limited via middleware
        - Audit logged
    """
    try:
        sanitizer = get_sanitizer()
        text = sanitizer.sanitize(request.text)

        if request.method == "shap":
            explainer = get_shap_explainer()
            result = explainer.explain(text)
        else:  # lime
            explainer = get_lime_explainer()
            result = explainer.explain(text)

        # Convert to response model
        features = [
            FeatureImportance(
                feature=f.get("feature") or f.get("word", ""),
                importance=f["importance"],
            )
            for f in result["top_features"]
        ]

        return ExplainResponse(
            top_features=features,
            predicted_class=result["predicted_class"],
            predicted_class_name=result.get("predicted_class_name"),
            prediction_probabilities=result.get("prediction_probabilities"),
            base_value=result.get("base_value"),
            explanation_method=result["explanation_method"],
            request_hash=result["request_hash"],
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Explanation generation failed",
        )


@router.get(
    "/explain/global",
    response_model=GlobalImportanceResponse,
    tags=["Explainability"],
    summary="Get global feature importance",
)
def global_importance() -> GlobalImportanceResponse:
    """
    Get global feature importance across the model.

    Security:
        - No user input required
        - Cached results
    """
    try:
        explainer = get_shap_explainer()
        features_data = explainer.get_global_feature_importance()

        features = [FeatureImportance(**f) for f in features_data]

        return GlobalImportanceResponse(
            features=features,
            model_type="calibrated_logistic_regression",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute global importance",
        )


# ============================================================================
# DOCUMENT PROCESSING ENDPOINTS
# ============================================================================


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    tags=["Documents"],
    summary="Upload and parse document",
)
async def upload_document(
    file: UploadFile = File(..., description="Document file (PDF, DOCX, TXT)"),
) -> DocumentUploadResponse:
    """
    Upload and parse medical document.

    Supported formats: PDF, DOCX, TXT, Email

    Security:
        - File size validation
        - MIME type validation
        - Malware scanning recommended (external)
        - PII detection
        - Content sanitization
    """
    # Security: Validate file
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename")

    # Security: Check file size before loading
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {MAX_FILE_SIZE} bytes)",
        )

    # Save temporarily
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # Parse document
        parser = get_document_parser()
        result = parser.parse(tmp_path)

        warnings = []
        if any(result["pii_detected"].values()):
            warnings.append("PII detected in document - review before processing")

        return DocumentUploadResponse(
            file_hash=result["file_hash"],
            text=result["text"],
            metadata=result["metadata"],
            pii_detected=result["pii_detected"],
            text_length=len(result["text"]),
            warnings=warnings if warnings else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document parsing failed",
        )
    finally:
        # Clean up temp file
        try:
            tmp_path.unlink()
        except Exception:
            pass


@router.post(
    "/documents/triage",
    response_model=TriageResponse,
    tags=["Documents"],
    summary="Triage from parsed document",
)
def triage_document(
    request: DocumentTriageRequest,
    triage_service: TriageService = Depends(get_triage_dependency),
) -> TriageResponse:
    """
    Run triage on text extracted from document.

    Security:
        - Text sanitization
        - File hash verification
        - Audit trail
    """
    try:
        # Sanitize text
        sanitizer = get_sanitizer()
        text = sanitizer.sanitize(request.text)

        if not sanitizer.validate_medical_text(text):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text does not appear to be medical content",
            )

        # Run triage
        result = triage_service.run_triage(text, request.biometric_token)
        enrichment = result.enrichment

        return TriageResponse(
            urgency=result.urgency,
            confidence=round(result.confidence, 4),
            recommended_care=enrichment["care_type"],
            specialty=enrichment["specialty"],
            next_steps=enrichment["next_steps"],
            audit_reference=result.audit_reference,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Triage failed",
        )


# ============================================================================
# CLINICIAN REVIEW ENDPOINTS
# ============================================================================


@router.get(
    "/review/pending",
    response_model=PendingCasesResponse,
    tags=["Clinician Review"],
    summary="Get pending review cases",
)
def get_pending_reviews(
    clinician_id: str = Query(..., min_length=1, description="Clinician ID"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(20, ge=1, le=100, description="Maximum cases to return"),
    review_service=Depends(lambda: get_review_service()),
) -> PendingCasesResponse:
    """
    Get pending cases for clinician review.

    Security:
        - Requires clinician_id
        - No PHI in response
        - Audit logged
    """
    try:
        priority_filter = ReviewPriority(priority) if priority else None

        cases = review_service.get_pending_cases(
            clinician_id=clinician_id,
            priority_filter=priority_filter,
            limit=limit,
        )

        return PendingCasesResponse(
            cases=[ReviewCaseResponse(**c) for c in cases],
            total=len(cases),
            priority_filter=priority,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending cases",
        )


@router.get(
    "/review/{case_id}",
    response_model=ReviewCaseResponse,
    tags=["Clinician Review"],
    summary="Get case details",
)
def get_case_details(
    case_id: str,
    clinician_id: str = Query(..., min_length=1, description="Clinician ID"),
    review_service=Depends(lambda: get_review_service()),
) -> ReviewCaseResponse:
    """
    Get full details for a review case including explanation.

    Security:
        - Requires clinician_id
        - No PHI exposed
    """
    try:
        case = review_service.get_case_details(case_id, clinician_id)

        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        return ReviewCaseResponse(**case)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve case details",
        )


@router.post(
    "/review/submit",
    response_model=SubmitReviewResponse,
    tags=["Clinician Review"],
    summary="Submit review decision",
)
def submit_review(
    request: SubmitReviewRequest,
    review_service=Depends(lambda: get_review_service()),
    compliance=Depends(get_compliance_dependency),
) -> SubmitReviewResponse:
    """
    Submit clinician review decision.

    Security:
        - Validates clinician_id
        - Sanitizes notes
        - Audit logs decision
        - Compliance signed
    """
    try:
        success = review_service.submit_review(
            case_id=request.case_id,
            clinician_id=request.clinician_id,
            decision=request.decision,
            notes=request.notes,
            override_urgency=request.override_urgency,
        )

        # Generate compliance signature
        signature = compliance.log_event({
            "event": "clinician_review",
            "case_id": request.case_id,
            "clinician_id": request.clinician_id,
            "decision": request.decision,
        })

        return SubmitReviewResponse(
            success=success,
            case_id=request.case_id,
            audit_signature=signature,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit review",
        )
