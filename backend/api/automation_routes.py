import logging
from fastapi import APIRouter, Depends
from backend.middleware.rbac import require_permission
from backend.models.automation_schemas import AutomationRequest, AutomationResponse
from backend.services.orchestrator import run_orchestrator

logger = logging.getLogger(__name__)
router  = APIRouter(prefix="/automation", tags=["Agent Automation"])


@router.post("/run", response_model=AutomationResponse)
def run_automation(
    request: AutomationRequest,
    current_user: dict = Depends(require_permission("chat:read")),
):
    """Run the full agent automation pipeline from a natural language message."""
    logger.info("Automation request: %s", request.message[:100])
    return run_orchestrator(request)
