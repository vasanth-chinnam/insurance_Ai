import logging
from fastapi import APIRouter
from backend.models.risk_schemas import RiskProfileRequest, RiskResponse
from backend.services.risk_profiler import profile_risk

logger = logging.getLogger(__name__)
router  = APIRouter(prefix="/risk", tags=["Risk Profiler"])


@router.post("/profile", response_model=RiskResponse)
def risk_profile(request: RiskProfileRequest):
    return profile_risk(request)
