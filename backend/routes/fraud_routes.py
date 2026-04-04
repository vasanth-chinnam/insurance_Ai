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
        request.insurance_type,
        request.claim_amount,
    )
    data = request.model_dump()
    # fraud_detector.py uses "claim_type" as the internal key
    data["claim_type"] = data.pop("insurance_type")
    result = detect_fraud(data)
    return FraudResponse(**result)
