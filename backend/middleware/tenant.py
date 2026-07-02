"""Tenant resolution middleware for multi-tenant SaaS architecture."""
from fastapi import Request
from backend.db import DEFAULT_TENANT_ID
import logging

logger = logging.getLogger(__name__)


async def tenant_middleware(request: Request, call_next):
    """
    Detect tenant from:
    1. X-Tenant-ID header (API clients, Postman, B2B integrations)
    2. Default tenant (current stage fallback — always works)

    Future: Add subdomain detection (companyA.insureai.com) when
    multiple companies are onboarded (Week 7+).
    """
    # Priority 1 — explicit header (for future API clients)
    tenant_id = request.headers.get("X-Tenant-ID")

    # Priority 2 — default (current stage)
    if not tenant_id:
        tenant_id = DEFAULT_TENANT_ID

    # Attach to request state so all route handlers can access it
    request.state.tenant_id = tenant_id

    response = await call_next(request)
    return response
