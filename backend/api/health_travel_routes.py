import logging
from fastapi import APIRouter
from backend.models.health_claim_schemas import HealthClaimRequest, HealthClaimResponse
from backend.models.travel_claim_schemas import TravelClaimRequest, TravelClaimResponse
from backend.services.health_claims import process_health_claim
from backend.services.travel_claims import process_travel_claim

logger = logging.getLogger(__name__)
router  = APIRouter(prefix="/claims", tags=["Health & Travel Claims"])


@router.post("/health", response_model=HealthClaimResponse)
def submit_health_claim(request: HealthClaimRequest):
    """Submit a health insurance claim for automated processing and policy validation."""
    return process_health_claim(request)


@router.post("/travel", response_model=TravelClaimResponse)
def submit_travel_claim(request: TravelClaimRequest):
    """Submit a travel insurance claim for baggage, flight delay, or medical issues."""
    return process_travel_claim(request)
