import os
import sys
import uuid
from backend.db import init_db, get_conn, DEFAULT_TENANT_ID
from backend.auth import create_token, get_current_user
from backend.routes.auth_routes import register, RegisterRequest
from backend.api.admin_routes import list_role_requests, handle_role_request, RoleRequestAction
from fastapi import Request

# Create a mock FastAPI Request class to pass state
class MockRequest:
    def __init__(self, tenant_id=DEFAULT_TENANT_ID):
        self.state = type('state', (), {'tenant_id': tenant_id})()

def test_verification_flow():
    print("--- Running Role Verification Flow Integration Tests ---")
    init_db()

    # 1. Register a new user requesting the 'manager' role
    test_email = f"manager_test_{uuid.uuid4().hex[:4]}@example.com"
    reg_body = RegisterRequest(
        name="John TestManager",
        email=test_email,
        phone="1234567890",
        password="password123",
        requested_role="manager",
        company_name="Acme Corporation",
        employee_id="EMP-MGR-007"
    )

    mock_req = MockRequest()
    response = register(reg_body, mock_req)
    
    # 2. Check that the user is initially registered as a customer
    user_id = None
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, role FROM users WHERE email = ?", (test_email,))
        row = c.fetchone()
        assert row is not None, "User registration failed!"
        assert row["role"] == "customer", f"Expected base role 'customer' but got {row['role']}"
        user_id = row["user_id"]
        print(f"Registered user {user_id} with initial base role 'customer'")

    # 3. Check that the role request is logged as pending
    request_id = None
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT request_id, requested_role, status, company_name, employee_id FROM role_requests WHERE user_id = ?", (user_id,))
        req_row = c.fetchone()
        assert req_row is not None, "Pending role request record not created!"
        assert req_row["requested_role"] == "manager", "Incorrect requested role!"
        assert req_row["status"] == "pending", f"Expected pending status but got {req_row['status']}"
        assert req_row["company_name"] == "Acme Corporation"
        assert req_row["employee_id"] == "EMP-MGR-007"
        request_id = req_row["request_id"]
        print(f"Verified pending role request created: ID {request_id} for 'manager'")

    # 4. Fetch list of role requests as Admin
    # Admin context payload
    admin_user = {
        "user_id": "U-ADMIN-999",
        "name": "System Admin",
        "email": "admin@insureai.com",
        "role": "admin",
        "tenant_id": DEFAULT_TENANT_ID
    }
    
    requests_list = list_role_requests(admin_user)
    matching_request = next((r for r in requests_list if r["request_id"] == request_id), None)
    assert matching_request is not None, "Admin did not retrieve the pending role request!"
    print("Admin successfully retrieved the pending requests list")

    # 5. Approve the request
    action_body = RoleRequestAction(action="approve")
    action_response = handle_role_request(request_id, action_body, admin_user)
    print("Action Response:", action_response)

    # 6. Verify database promotion
    with get_conn() as conn:
        c = conn.cursor()
        # Verify request status updated to approved
        c.execute("SELECT status FROM role_requests WHERE request_id = ?", (request_id,))
        assert c.fetchone()["status"] == "approved", "Request status not set to approved!"
        
        # Verify user's actual role promoted to manager
        c.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        db_role = c.fetchone()["role"]
        assert db_role == "manager", f"User role was not promoted! Still: {db_role}"
        print(f"Verified User {user_id} promoted to 'manager' in DB! Success.")

    print("All integration test assertions passed successfully!")

if __name__ == "__main__":
    test_verification_flow()
