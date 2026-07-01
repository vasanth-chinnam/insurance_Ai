import logging
from fastapi import APIRouter
from backend.models.renewal_schemas import RenewalRequest, RenewalResponse
from backend.services.renewal_agent import run_renewal_agent

logger = logging.getLogger(__name__)
router  = APIRouter(prefix="/renewal", tags=["Renewal Agent"])


@router.post("/negotiate", response_model=RenewalResponse)
def negotiate_renewal(request: RenewalRequest):
    """Negotiate policy renewal by comparing current terms with market alternatives and suggesting optimal options."""
    logger.info("Renewal negotiation requested — type=%s user=%s",
                request.user_profile.insurance_type, request.user_profile.name)
    return run_renewal_agent(request)
