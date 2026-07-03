import os
import sys
from backend.db import init_db, get_conn
from backend.auth import get_current_user

def test_production_auth_strict():
    print("--- Testing Database Seeding & Production-Like Auth Strictness ---")
    
    # 1. Initialize database and check that default users exist
    init_db()
    
    default_users = [
        ("U-ADMIN-999", "admin"),
        ("U-MANAGER-999", "manager"),
        ("U-AGENT-999", "agent"),
        ("U-INVEST-999", "fraud_investigator"),
        ("U-CUST-999", "customer"),
    ]
    
    with get_conn() as conn:
        c = conn.cursor()
        for uid, expected_role in default_users:
            c.execute("SELECT user_id, email, role FROM users WHERE user_id = ?", (uid,))
            row = c.fetchone()
            assert row is not None, f"Default user {uid} was not seeded!"
            assert row["role"] == expected_role, f"Default user {uid} has wrong role {row['role']}, expected {expected_role}"
            print(f"Verified seeded account: {row['email']} -> role: {row['role']}")

    # 2. Verify that mock token role escalation does NOT update the DB
    # We pass a mock token pretending U-CUST-999 is an admin
    token = "mock-google-token-admin-U-CUST-999"
    
    # Retrieve user via middleware dependency
    user = get_current_user(token)
    
    # Check that in the database, the role remains 'customer'
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE user_id = ?", ("U-CUST-999",))
        db_role = c.fetchone()["role"]
        
    assert db_role == "customer", f"Security Alert: Role in DB was upgraded to {db_role} via mock token!"
    print("Security Check Passed: Database role remained 'customer' even when mock-admin token was decoded.")
    print("All production auth security validations passed successfully!")

if __name__ == "__main__":
    test_production_auth_strict()
