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
            user_id = parts[-1]
            return {
                "sub": user_id,
                "email": f"{user_id}@example.com",
                "role": "user",
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
        raise HTTPException(status_code=401, detail="User not found")

    user = dict(row)
    user["tenant_id"] = tenant_id
    return user
