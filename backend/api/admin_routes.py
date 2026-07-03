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


class RoleRequestAction(BaseModel):
    action: str  # "approve" | "reject"


@router.get("/role-requests")
def list_role_requests(current_user: dict = Depends(require_admin_or_manager)):
    """List all role requests in the current tenant."""
    tenant_id = current_user.get("tenant_id", DEFAULT_TENANT_ID)
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT r.request_id, r.user_id, r.requested_role, r.company_name, 
                   r.employee_id, r.license_number, r.additional_info, r.status, 
                   r.created_at, u.name as user_name, u.email as user_email
            FROM role_requests r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.tenant_id = ?
            ORDER BY r.created_at DESC
        """, (tenant_id,)).fetchall()
    return [dict(r) for r in rows]


@router.post("/role-requests/{request_id}/action")
def handle_role_request(
    request_id: str,
    body: RoleRequestAction,
    current_user: dict = Depends(require_admin),
):
    """Admin only — approve or reject a role request."""
    action = body.action.strip().lower()
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve' or 'reject'")
        
    tenant_id = current_user.get("tenant_id", DEFAULT_TENANT_ID)
    
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT user_id, requested_role, status 
            FROM role_requests 
            WHERE request_id = ? AND tenant_id = ?
        """, (request_id, tenant_id))
        row = c.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Role request not found")
            
        if row["status"] != "pending":
            raise HTTPException(status_code=400, detail=f"Request already processed (status: {row['status']})")
            
        target_user_id = row["user_id"]
        requested_role = row["requested_role"]
        
        new_status = "approved" if action == "approve" else "rejected"
        
        c.execute("""
            UPDATE role_requests 
            SET status = ? 
            WHERE request_id = ? AND tenant_id = ?
        """, (new_status, request_id, tenant_id))
        
        if action == "approve":
            c.execute("""
                UPDATE users 
                SET role = ? 
                WHERE user_id = ? AND tenant_id = ?
            """, (requested_role, target_user_id, tenant_id))
            logger.info("Approved role request %s: User %s promoted to %s by Admin %s",
                        request_id, target_user_id, requested_role, current_user["user_id"])
        else:
            logger.info("Rejected role request %s: User %s rejected for role %s by Admin %s",
                        request_id, target_user_id, requested_role, current_user["user_id"])
                        
    return {"message": f"Role request has been {new_status}"}
