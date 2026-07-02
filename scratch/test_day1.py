import sys
import os
import urllib.request
import json
import jwt

# Add root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set production database connection string for tests
os.environ["DATABASE_URL"] = "postgresql://postgres.jonqqrlpmibesakcjrfd:Vasanth%400611@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

from backend.db import get_conn, DEFAULT_TENANT_ID, create_tenant, tenant_query
from backend.auth import JWT_SECRET_KEY, JWT_ALGORITHM

def test_1_login_and_decode_jwt():
    print("--- Running Test 1: Login & Decode JWT ---")
    url = "http://127.0.0.1:8000/auth/login"
    data = json.dumps({
        "email": "test_tenant@example.com",
        "password": "password123"
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        response = urllib.request.urlopen(req)
        resp_data = json.loads(response.read().decode("utf-8"))
        token = resp_data["token"]
        print("Login response received!")
        print(f"Role: {resp_data['role']}")
        print(f"Tenant ID: {resp_data['tenant_id']}")
        
        # Decode token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        print("Decoded JWT Payload:")
        print(payload)
        
        assert payload["role"] == "customer", "Role is incorrect"
        assert payload["tenant_id"] == DEFAULT_TENANT_ID, "Tenant ID is incorrect"
        print("[OK] Test 1 Passed!")
    except Exception as e:
        print(f"[FAIL] Test 1 Failed: {e}")

def test_2_tenant_isolation():
    print("\n--- Running Test 2: Tenant Isolation ---")
    with get_conn() as conn:
        # Create Tenant A
        tenant_a = create_tenant("Tenant Company A", "tenant-a.com")
        tenant_b = create_tenant("Tenant Company B", "tenant-b.com")
        
        print(f"Created Tenant A: {tenant_a['id']}")
        print(f"Created Tenant B: {tenant_b['id']}")
        
        # Create users for both
        conn.execute(
            "INSERT INTO users (user_id, name, email, role, tenant_id) VALUES (%s, %s, %s, %s, %s)",
            ("U-A001", "User A", "user_a@tenant-a.com", "customer", tenant_a["id"])
        )
        conn.execute(
            "INSERT INTO users (user_id, name, email, role, tenant_id) VALUES (%s, %s, %s, %s, %s)",
            ("U-B001", "User B", "user_b@tenant-b.com", "customer", tenant_b["id"])
        )
        
        # Create policy for A
        conn.execute(
            "INSERT INTO policies (policy_id, user_id, insurance_type, tenant_id) VALUES (%s, %s, %s, %s)",
            ("POL-A", "U-A001", "motor", tenant_a["id"])
        )
        
        # Create policy for B
        conn.execute(
            "INSERT INTO policies (policy_id, user_id, insurance_type, tenant_id) VALUES (%s, %s, %s, %s)",
            ("POL-B", "U-B001", "motor", tenant_b["id"])
        )
        
        # Query Tenant A data using tenant_query
        rows_a = tenant_query(conn, "SELECT * FROM policies", (), tenant_id=tenant_a["id"])
        print(f"Tenant A query returned: {[dict(r)['policy_id'] for r in rows_a]}")
        
        # Query Tenant B data using tenant_query
        rows_b = tenant_query(conn, "SELECT * FROM policies", (), tenant_id=tenant_b["id"])
        print(f"Tenant B query returned: {[dict(r)['policy_id'] for r in rows_b]}")
        
        # Assertions
        assert len(rows_a) == 1 and rows_a[0]["policy_id"] == "POL-A", "Tenant A should only see POL-A"
        assert len(rows_b) == 1 and rows_b[0]["policy_id"] == "POL-B", "Tenant B should only see POL-B"
        
        # Clean up
        conn.execute("DELETE FROM policies WHERE policy_id IN (%s, %s)", ("POL-A", "POL-B"))
        conn.execute("DELETE FROM users WHERE user_id IN (%s, %s)", ("U-A001", "U-B001"))
        conn.execute("DELETE FROM tenants WHERE id IN (%s, %s)", (tenant_a["id"], tenant_b["id"]))
        print("[OK] Test 2 Passed!")

def test_3_missing_tenant_id():
    print("\n--- Running Test 3: Missing Tenant ID Fallback ---")
    try:
        # 1. Create a user and commit the transaction first
        with get_conn() as conn:
            conn.execute("DELETE FROM policies WHERE policy_id = %s", ("POL-TEST-3",))
            conn.execute("DELETE FROM users WHERE user_id = %s", ("U-TEST-3",))
            
            conn.execute(
                "INSERT INTO users (user_id, name, email, role, tenant_id) VALUES (%s, %s, %s, %s, %s)",
                ("U-TEST-3", "Test 3", "test3@example.com", "customer", DEFAULT_TENANT_ID)
            )
        
        # 2. Save policy using create_policy WITHOUT specifying tenant_id (will auto-assign DEFAULT_TENANT_ID)
        from backend.db import create_policy
        create_policy(
            policy_id="POL-TEST-3",
            user_id="U-TEST-3",
            insurance_type="motor"
        )
        
        # 3. Fetch and verify
        with get_conn() as conn:
            row = conn.execute("SELECT tenant_id FROM policies WHERE policy_id = %s", ("POL-TEST-3",)).fetchone()
            tenant_id_value = dict(row)['tenant_id']
            print(f"Policy stored tenant_id: {tenant_id_value}")
            assert tenant_id_value == DEFAULT_TENANT_ID, "Should automatically fall back to default tenant ID"
            
            # Clean up
            conn.execute("DELETE FROM policies WHERE policy_id = %s", ("POL-TEST-3",))
            conn.execute("DELETE FROM users WHERE user_id = %s", ("U-TEST-3",))
            
        print("[OK] Test 3 Passed!")
    except Exception as e:
        print(f"[FAIL] Test 3 Failed: {e}")

if __name__ == "__main__":
    test_1_login_and_decode_jwt()
    test_2_tenant_isolation()
    test_3_missing_tenant_id()
