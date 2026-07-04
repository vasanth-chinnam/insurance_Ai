import os
import sys
from backend.db import init_db, get_conn, DEFAULT_TENANT_ID
from backend.services.audit import log_action, get_audit_logs, get_audit_stats, AuditAction

def test_audit_flow():
    print("--- Running Audit Logging Integration Tests ---")
    
    # Initialize DB
    init_db()
    
    # 1. Clear existing audit logs for test isolation
    with get_conn() as conn:
        conn.execute("DELETE FROM audit_logs")
        
    print("Cleaned audit_logs table.")

    # 2. Log several different actions
    user_id = "U-TEST-USER-1"
    
    print("Logging mock events...")
    log_action(
        action=AuditAction.LOGIN,
        user_id=user_id,
        tenant_id=DEFAULT_TENANT_ID,
        entity="user",
        entity_id=user_id,
        details={"ip": "127.0.0.1"},
        status="success"
    )
    
    log_action(
        action=AuditAction.RUN_FRAUD_CHECK,
        user_id=user_id,
        tenant_id=DEFAULT_TENANT_ID,
        entity="claim",
        entity_id="C-12345",
        details={"score": 85.5, "verdict": "FLAGGED"},
        status="success"
    )
    
    log_action(
        action=AuditAction.FAILED_LOGIN,
        details={"attempted_email": "bad@email.com"},
        status="failed"
    )

    # 3. Retrieve logs and verify content
    print("Retrieving logged events...")
    logs = get_audit_logs(tenant_id=DEFAULT_TENANT_ID, limit=10)
    
    assert len(logs) == 3, f"Expected 3 logs, got {len(logs)}"
    
    # Verify values
    failed_log = [l for l in logs if l["action"] == AuditAction.FAILED_LOGIN][0]
    assert failed_log["status"] == "failed", f"Expected failed status, got {failed_log['status']}"
    
    login_log = [l for l in logs if l["action"] == AuditAction.LOGIN][0]
    assert login_log["user_id"] == user_id, f"Expected user_id {user_id}, got {login_log['user_id']}"
    assert login_log["entity"] == "user", f"Expected entity 'user', got {login_log['entity']}"
    
    print("Audit log values verified successfully!")

    # 4. Verify stats
    print("Fetching audit stats...")
    stats = get_audit_stats(tenant_id=DEFAULT_TENANT_ID)
    
    assert stats["today_total"] == 3, f"Expected today_total 3, got {stats['today_total']}"
    assert stats["today_failed"] == 1, f"Expected today_failed 1, got {stats['today_failed']}"
    assert stats["active_users"] == 1, f"Expected active_users 1 (U-TEST-USER-1, others are NULL), got {stats['active_users']}"
    
    print("Audit stats verified successfully!")
    print("All integration test assertions passed successfully!")

if __name__ == "__main__":
    test_audit_flow()
