import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from backend.middleware.rbac import require_permission
from backend.models.crop_schemas import CropAnalyzeRequest, CropAgentResponse
from backend.services.crop_agent import run_crop_agent
from backend.services.audit import log_action, AuditAction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/crop", tags=["Crop Agent"])


@router.post("/analyze", response_model=CropAgentResponse)
def analyze_crop(
    request: CropAnalyzeRequest,
    current_user: dict = Depends(require_permission("crop:read")),
    req: Request = None,
):
    """Analyze crop conditions, check historical weather indices, and evaluate payout eligibility."""
    result = run_crop_agent(request)
    log_action(
        action    = AuditAction.RUN_CROP_AGENT,
        user_id   = current_user["user_id"],
        tenant_id = current_user.get("tenant_id"),
        entity    = "farmer",
        entity_id = request.farmer_id,
        details   = {
            "payout_status": result.payout_status,
            "payout_amount": result.payout_amount,
        },
        ip_address = getattr(req, "client", None).host if getattr(req, "client", None) else None,
    )
    return result


@router.get("/farmers")
def list_farmers(current_user: dict = Depends(require_permission("crop:read"))):
    """Return list of demo farmers for the UI dropdown."""
    try:
        with open(Path("data/mock_db/farmers.json")) as f:
            farmers = json.load(f)
        return [
            {
                "farmer_id": fa["farmer_id"],
                "name":      fa["name"],
                "location":  fa["location"],
                "crop_type": fa["crop_type"],
            }
            for fa in farmers
        ]
    except Exception:
        return []
