import os
from datetime import datetime, timedelta
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from backend.db import get_conn, DEFAULT_TENANT_ID

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-for-jwt-tokens-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def create_token(user_id: str, email: str, role: str, tenant_id: str = DEFAULT_TENANT_ID) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub":       user_id,
        "email":     email,
        "role":      role,
        "tenant_id": tenant_id,
        "exp":       expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        # Check if it's a mock token from earlier and fallback gracefully
        if token.startswith("mock-"):
            parts = token.split("-")
            if len(parts) >= 5:
                # Format: mock-google-token-{role}-{user_id}
                role = parts[-2]
                user_id = parts[-1]
            else:
                role = "customer"
                user_id = parts[-1]
            return {
                "sub": user_id,
                "email": f"{user_id}@example.com",
                "role": role,
                "tenant_id": DEFAULT_TENANT_ID
            }
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id", DEFAULT_TENANT_ID)

    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, name, email, role, tenant_id FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()

    if not row:
        if token and token.startswith("mock-"):
            mock_role = payload.get("role", "customer")
            if mock_role == "user":
                mock_role = "admin"
            mock_email = payload.get("email", f"{user_id}@example.com")
            mock_name = f"Mock User {user_id}"
            with get_conn() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO users (user_id, name, email, role, tenant_id) VALUES (?, ?, ?, ?, ?)",
                    (user_id, mock_name, mock_email, mock_role, tenant_id)
                )
                c = conn.cursor()
                c.execute("SELECT user_id, name, email, role, tenant_id FROM users WHERE user_id = ?", (user_id,))
                row = c.fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="User not found")

    # Dynamically update the database user role if using a mock token and roles differ
    if row and token and token.startswith("mock-"):
        token_role = payload.get("role", "customer")
        if token_role == "user":
            token_role = "admin"
        if row["role"] != token_role:
            with get_conn() as conn:
                conn.execute(
                    "UPDATE users SET role = ? WHERE user_id = ? AND tenant_id = ?",
                    (token_role, user_id, tenant_id)
                )
            # Re-query
            with get_conn() as conn:
                c = conn.cursor()
                c.execute("SELECT user_id, name, email, role, tenant_id FROM users WHERE user_id = ?", (user_id,))
                row = c.fetchone()

    user = dict(row)
    user["tenant_id"] = tenant_id
    return user
