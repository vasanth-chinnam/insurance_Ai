import logging
import json
import uuid
from datetime import datetime
from backend.db import get_conn, DEFAULT_TENANT_ID

logger = logging.getLogger(__name__)

# ── Audit action constants ─────────────────────────────────────────────
class AuditAction:
    # Auth
    LOGIN               = "LOGIN"
    LOGOUT              = "LOGOUT"
    REGISTER            = "REGISTER"
    GOOGLE_AUTH         = "GOOGLE_AUTH"

    # Policy
    UPLOAD_POLICY       = "UPLOAD_POLICY"
    DELETE_POLICY       = "DELETE_POLICY"
    VIEW_POLICY         = "VIEW_POLICY"
    POLICY_QUERY        = "POLICY_QUERY"

    # Claims
    CREATE_CLAIM        = "CREATE_CLAIM"
    UPDATE_CLAIM        = "UPDATE_CLAIM"
    APPROVE_CLAIM       = "APPROVE_CLAIM"
    REJECT_CLAIM        = "REJECT_CLAIM"

    # Fraud
    RUN_FRAUD_CHECK     = "RUN_FRAUD_CHECK"
    FLAG_FRAUD          = "FLAG_FRAUD"
    CLEAR_FRAUD         = "CLEAR_FRAUD"

    # Risk
    GENERATE_RISK       = "GENERATE_RISK"

    # Crop
    RUN_CROP_AGENT      = "RUN_CROP_AGENT"
    TRIGGER_PAYOUT      = "TRIGGER_PAYOUT"

    # Renewal
    RUN_RENEWAL         = "RUN_RENEWAL"
    ACCEPT_DEAL         = "ACCEPT_DEAL"

    # Automation
    RUN_AUTOMATION      = "RUN_AUTOMATION"

    # Admin
    UPDATE_ROLE         = "UPDATE_ROLE"
    APPROVE_ROLE_REQUEST= "APPROVE_ROLE_REQUEST"
    REJECT_ROLE_REQUEST = "REJECT_ROLE_REQUEST"
    CREATE_TENANT       = "CREATE_TENANT"

    # Security
    FAILED_LOGIN        = "FAILED_LOGIN"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    RATE_LIMITED        = "RATE_LIMITED"


def log_action(
    action:     str,
    user_id:    str  = None,
    tenant_id:  str  = None,
    entity:     str  = None,
    entity_id:  str  = None,
    details:    dict = None,
    ip_address: str  = None,
    user_agent: str  = None,
    status:     str  = "success",
) -> None:
    """
    Write an audit log entry.
    Non-blocking — logs warning if DB write fails but never crashes the request.
    """
    try:
        log_id = str(uuid.uuid4())
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO audit_logs
                (id, user_id, tenant_id, action, entity, entity_id,
                 details, ip_address, user_agent, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                user_id,
                tenant_id or DEFAULT_TENANT_ID,
                action,
                entity,
                entity_id,
                json.dumps(details or {}),
                ip_address,
                user_agent,
                status,
            ))
    except Exception as e:
        # Never let audit logging crash the main request
        logger.warning("Audit log failed: %s", e)


def get_audit_logs(
    tenant_id:  str,
    user_id:    str  = None,
    action:     str  = None,
    limit:      int  = 50,
    offset:     int  = 0,
) -> list[dict]:
    """Fetch audit logs for a tenant with optional filters."""
    try:
        with get_conn() as conn:
            query  = """
                SELECT
                    al.*,
                    u.name as user_name,
                    u.email as user_email,
                    u.role as user_role
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.user_id
                WHERE al.tenant_id = ?
            """
            params = [tenant_id]

            if user_id:
                query  += " AND al.user_id = ?"
                params.append(user_id)

            if action:
                query  += " AND al.action = ?"
                params.append(action)

            query  += " ORDER BY al.created_at DESC LIMIT ? OFFSET ?"
            params += [limit, offset]

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.warning("Get audit logs failed: %s", e)
        return []


def get_audit_stats(tenant_id: str) -> dict:
    """Get summary stats for the audit dashboard."""
    try:
        with get_conn() as conn:
            # Total actions today
            today = conn.execute("""
                SELECT COUNT(*) as count FROM audit_logs
                WHERE tenant_id = ?
                AND created_at >= CURRENT_DATE
            """, (tenant_id,)).fetchone()

            # Actions by type
            by_action = conn.execute("""
                SELECT action, COUNT(*) as count
                FROM audit_logs
                WHERE tenant_id = ?
                GROUP BY action
                ORDER BY count DESC
                LIMIT 10
            """, (tenant_id,)).fetchall()

            # Failed actions
            failed = conn.execute("""
                SELECT COUNT(*) as count FROM audit_logs
                WHERE tenant_id = ? AND status = 'failed'
                AND created_at >= CURRENT_DATE
            """, (tenant_id,)).fetchone()

            # Active users today
            active_users = conn.execute("""
                SELECT COUNT(DISTINCT user_id) as count
                FROM audit_logs
                WHERE tenant_id = ?
                AND created_at >= CURRENT_DATE
            """, (tenant_id,)).fetchone()

            return {
                "today_total":   dict(today)["count"] if today else 0,
                "today_failed":  dict(failed)["count"] if failed else 0,
                "active_users":  dict(active_users)["count"] if active_users else 0,
                "by_action":     [dict(r) for r in by_action],
            }
    except Exception as e:
        logger.warning("Audit stats failed: %s", e)
        return {}
