import logging

from fastapi import APIRouter

from backend.models.fraud_schemas import FraudRequest, FraudResponse
from backend.services.fraud_detector import detect_fraud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])


@router.post("/analyze", response_model=FraudResponse)
def analyze_fraud(request: FraudRequest):
    """Run fraud analysis on the given claim data."""
    logger.info(
        "Fraud analysis requested — type=%s amount=%.0f",
        request.claim_type,
        request.claim_amount,
    )
    result = detect_fraud(request.model_dump())
    return FraudResponse(**result)
