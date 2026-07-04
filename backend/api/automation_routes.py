import logging
from fastapi import APIRouter, Depends, Request
from backend.middleware.rbac import require_permission
from backend.models.automation_schemas import AutomationRequest, AutomationResponse
from backend.services.orchestrator import run_orchestrator
from backend.services.audit import log_action, AuditAction

logger = logging.getLogger(__name__)
router  = APIRouter(prefix="/automation", tags=["Agent Automation"])


@router.post("/run", response_model=AutomationResponse)
def run_automation(
    request: AutomationRequest,
    current_user: dict = Depends(require_permission("chat:read")),
    req: Request = None,
):
    """Run the full agent automation pipeline from a natural language message."""
    logger.info("Automation request: %s", request.message[:100])
    result = run_orchestrator(request)
    log_action(
        action    = AuditAction.RUN_AUTOMATION,
        user_id   = current_user["user_id"],
        tenant_id = current_user.get("tenant_id"),
        details   = {
            "intent":      result.intent,
            "agents_run":  [a.agent_name for a in result.agents_run],
            "message":     request.message[:100],
        },
        ip_address = getattr(req, "client", None).host if getattr(req, "client", None) else None,
    )
    return result
