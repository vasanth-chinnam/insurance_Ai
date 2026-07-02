"""Tenant resolution middleware for multi-tenant SaaS architecture."""
from fastapi import Request
from backend.db import DEFAULT_TENANT_ID
import logging

logger = logging.getLogger(__name__)


async def tenant_middleware(request: Request, call_next):
    """
    Detect tenant from:
    1. Authorization Bearer token (JWT claim 'tenant_id')
    2. X-Tenant-ID header (API clients, Postman, B2B integrations)
    3. Default tenant (current stage fallback)
    """
    from backend.db import tenant_context, DEFAULT_TENANT_ID
    
    tenant_id = None

    # Priority 1 — Authorization Bearer JWT Token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):].strip()
        try:
            from backend.auth import decode_token
            payload = decode_token(token)
            if payload:
                tenant_id = payload.get("tenant_id")
                # Also store user info in request state for convenient downstream access
                request.state.user = payload
        except Exception:
            pass

    # Priority 2 — explicit header (for third-party API clients)
    if not tenant_id:
        tenant_id = request.headers.get("X-Tenant-ID")

    # Priority 3 — fallback default
    if not tenant_id:
        tenant_id = DEFAULT_TENANT_ID

    # Attach to request state
    request.state.tenant_id = tenant_id

    # Set the thread/async ContextVar for request-scoped database context
    token_var = tenant_context.set(tenant_id)

    try:
        response = await call_next(request)
        return response
    finally:
        tenant_context.reset(token_var)
