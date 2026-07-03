from fastapi import HTTPException, Depends
from backend.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

# ── Permission Matrix ─────────────────────────────────────────────────
# Maps each role to what they can access
ROLE_PERMISSIONS = {
    "customer": [
        "policy:read",
        "claims:create",
        "claims:read",
        "renewal:read",
        "risk:read",
        "chat:read",
    ],
    "agent": [
        "policy:read",
        "policy:create",
        "policy:upload",
        "claims:create",
        "claims:read",
        "claims:update",
        "renewal:read",
        "risk:read",
        "chat:read",
        "users:read",
        "crop:read",  # Allow agent to run crop analysis
    ],
    "fraud_investigator": [
        "policy:read",
        "claims:read",
        "fraud:read",
        "fraud:investigate",
        "risk:read",
        "audit:read",
        "chat:read",
    ],
    "manager": [
        "policy:read",
        "policy:create",
        "policy:upload",
        "claims:read",
        "claims:create",
        "claims:update",
        "claims:approve",
        "fraud:read",
        "fraud:investigate",
        "risk:read",
        "risk:update",
        "renewal:read",
        "crop:read",
        "chat:read",
        "audit:read",
        "analytics:read",
        "users:read",
    ],
    "admin": ["*"],  # all permissions
}


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    perms = ROLE_PERMISSIONS.get(role, [])
    return "*" in perms or permission in perms


# ── Role dependency factories ─────────────────────────────────────────

def require_permission(permission: str):
    """
    FastAPI dependency — use on any route to protect it.
    Example:
        @router.get("/fraud", dependencies=[Depends(require_permission("fraud:read"))])
    """
    def checker(current_user: dict = Depends(get_current_user)):
        role = current_user.get("role", "customer")
        if not has_permission(role, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required permission: {permission}. Your role: {role}"
            )
        return current_user
    return checker


def require_role(*roles: str):
    """
    FastAPI dependency — restrict to specific roles.
    Example:
        @router.get("/admin", dependencies=[Depends(require_role("admin", "manager"))])
    """
    def checker(current_user: dict = Depends(get_current_user)):
        role = current_user.get("role", "customer")
        if role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {roles}. Your role: {role}"
            )
        return current_user
    return checker


# ── Convenience dependencies ─────────────────────────────────────────
require_admin              = require_role("admin")
require_admin_or_manager   = require_role("admin", "manager")
require_fraud_investigator = require_role("admin", "manager", "fraud_investigator")
require_agent_or_above     = require_role("admin", "manager", "agent", "fraud_investigator")
