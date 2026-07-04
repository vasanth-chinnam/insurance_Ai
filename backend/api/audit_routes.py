import logging
from fastapi import APIRouter, Depends, Query
from backend.middleware.rbac import require_permission
from backend.services.audit import get_audit_logs, get_audit_stats
from backend.db import DEFAULT_TENANT_ID

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("/logs")
def fetch_audit_logs(
    user_id:  str  = Query(None),
    action:   str  = Query(None),
    limit:    int  = Query(50, le=200),
    offset:   int  = Query(0),
    current_user: dict = Depends(require_permission("audit:read")),
):
    tenant_id = current_user.get("tenant_id", DEFAULT_TENANT_ID)
    logs = get_audit_logs(
        tenant_id = tenant_id,
        user_id   = user_id,
        action    = action,
        limit     = limit,
        offset    = offset,
    )
    return {"logs": logs, "total": len(logs)}


@router.get("/stats")
def fetch_audit_stats(
    current_user: dict = Depends(require_permission("audit:read")),
):
    tenant_id = current_user.get("tenant_id", DEFAULT_TENANT_ID)
    return get_audit_stats(tenant_id)
