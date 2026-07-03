import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.middleware.rbac import require_admin, require_admin_or_manager
from backend.auth import get_current_user
from backend.db import get_conn, DEFAULT_TENANT_ID

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])

VALID_ROLES = ["customer", "agent", "fraud_investigator", "manager", "admin"]


class UpdateRoleRequest(BaseModel):
    user_id: str
    role:    str


@router.get("/users")
def list_users(current_user: dict = Depends(require_admin_or_manager)):
    """List all users in the current tenant."""
    tenant_id = current_user.get("tenant_id", DEFAULT_TENANT_ID)
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT user_id, name, email, role, created_at
            FROM users
            WHERE tenant_id = ?
            ORDER BY created_at DESC
        """, (tenant_id,)).fetchall()
    return [dict(r) for r in rows]


@router.put("/users/role")
def update_user_role(
    request: UpdateRoleRequest,
    current_user: dict = Depends(require_admin),
):
    """Admin only — change a user's role."""
    if request.role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {VALID_ROLES}"
        )
    tenant_id = current_user.get("tenant_id", DEFAULT_TENANT_ID)
    with get_conn() as conn:
        result = conn.execute("""
            UPDATE users SET role = ?
            WHERE user_id = ? AND tenant_id = ?
        """, (request.role, request.user_id, tenant_id))
        
        # In sqlite3, execute returns a cursor where rowcount can be checked.
        # But to be robust across both wrappers:
        rowcount = getattr(result, "rowcount", 0)
        # If SQLite cursor was used, we can also check result.rowcount.
        # Let's fallback or perform a SELECT count checks if needed, but rowcount works
        if rowcount == 0:
            # Check if user exists
            check = conn.execute("SELECT 1 FROM users WHERE user_id = ? AND tenant_id = ?", (request.user_id, tenant_id)).fetchone()
            if not check:
                raise HTTPException(status_code=404, detail="User not found")

    logger.info("Role updated: %s → %s by %s",
                request.user_id, request.role, current_user["user_id"])
    return {"message": f"Role updated to {request.role}"}


@router.get("/tenants/me")
def get_my_tenant(current_user: dict = Depends(get_current_user)):
    """Get current tenant info."""
    tenant_id = current_user.get("tenant_id", DEFAULT_TENANT_ID)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, logo_url, primary_color, domain, created_at FROM tenants WHERE id = ?", (tenant_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return dict(row)
