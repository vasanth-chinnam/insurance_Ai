import logging

from fastapi import APIRouter, Depends, Request

from backend.middleware.rbac import require_permission
from backend.models.fraud_schemas import FraudRequest, FraudResponse
from backend.services.fraud_detector import detect_fraud
from backend.services.audit import log_action, AuditAction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])


@router.post("/analyze", response_model=FraudResponse)
def analyze_fraud(
    request: FraudRequest,
    current_user: dict = Depends(require_permission("fraud:read")),
    req: Request = None,
):
    """Run fraud analysis on the given claim data."""
    logger.info(
        "Fraud analysis requested — type=%s amount=%.0f",
        request.insurance_type,
        request.claim_amount,
    )
    data = request.model_dump()
    # fraud_detector.py uses "claim_type" as the internal key
    data["claim_type"] = data.pop("insurance_type")
    result = detect_fraud(data)
    log_action(
        action    = AuditAction.RUN_FRAUD_CHECK,
        user_id   = current_user["user_id"],
        tenant_id = current_user.get("tenant_id"),
        entity    = "claim",
        details   = {
            "policy_number": request.policy_number,
            "score":         result["fraud_score"],
            "verdict":       result["verdict"],
        },
        ip_address = getattr(req, "client", None).host if getattr(req, "client", None) else None,
    )
    return FraudResponse(**result)
