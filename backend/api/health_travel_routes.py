import logging
from fastapi import APIRouter, Depends
from backend.middleware.rbac import require_permission
from backend.models.health_claim_schemas import HealthClaimRequest, HealthClaimResponse
from backend.models.travel_claim_schemas import TravelClaimRequest, TravelClaimResponse
from backend.services.health_claims import process_health_claim
from backend.services.travel_claims import process_travel_claim

logger = logging.getLogger(__name__)
router  = APIRouter(prefix="/claims", tags=["Health & Travel Claims"])


@router.post("/health", response_model=HealthClaimResponse)
def submit_health_claim(
    request: HealthClaimRequest,
    current_user: dict = Depends(require_permission("claims:create")),
):
    """Submit a health insurance claim for automated processing and policy validation."""
    return process_health_claim(request)


@router.post("/travel", response_model=TravelClaimResponse)
def submit_travel_claim(
    request: TravelClaimRequest,
    current_user: dict = Depends(require_permission("claims:create")),
):
    """Submit a travel insurance claim for baggage, flight delay, or medical issues."""
    return process_travel_claim(request)
