import uuid
import base64
import json
import logging
import hashlib
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from backend.db import get_conn, DEFAULT_TENANT_ID
from backend.auth import create_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

class GoogleAuthRequest(BaseModel):
    credential: str

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    phone: str | None = None
    password: str

def hash_password(password: str) -> str:
    """Hash password using SHA-256 for simple offline run."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def decode_google_credential(credential: str) -> dict:
    """Decode base64 JWT payload from Google OAuth Credential."""
    try:
        parts = credential.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        payload_b64 = parts[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_bytes = base64.b64decode(payload_b64)
        return json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        logger.error("Failed to decode Google credential: %s", e)
        raise HTTPException(status_code=400, detail="Invalid Google credentials format")

@router.post("/google")
def google_auth(req_body: GoogleAuthRequest, req: Request):
    payload = decode_google_credential(req_body.credential)
    email = payload.get("email")
    name = payload.get("name", "Google User")
    avatar = payload.get("picture", "")

    if not email:
        raise HTTPException(status_code=400, detail="Google authentication did not provide email")

    tenant_id = getattr(req.state, "tenant_id", DEFAULT_TENANT_ID)

    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = c.fetchone()

        if row:
            user_id = row["user_id"]
            name = row["name"]
            role = row["role"] if "role" in row and row["role"] else "customer"
            user_tenant_id = row["tenant_id"] if "tenant_id" in row and row["tenant_id"] else tenant_id
        else:
            user_id = "U" + str(uuid.uuid4().hex[:8]).upper()
            role = "customer"
            user_tenant_id = tenant_id
            c.execute(
                "INSERT INTO users (user_id, name, email, phone, password_hash, role, tenant_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, name, email, "", "", role, user_tenant_id),
            )
            logger.info("Created new user via Google Sign-In: %s (%s)", name, email)

    token = create_token(user_id, email, role, user_tenant_id)
    return {
        "token": token,
        "name": name,
        "email": email,
        "role": role,
        "avatar": avatar,
        "tenant_id": user_tenant_id,
    }

@router.post("/login")
def login(req_body: LoginRequest, req: Request):
    email = req_body.email.strip().lower()
    password_hash = hash_password(req_body.password)

    tenant_id = getattr(req.state, "tenant_id", DEFAULT_TENANT_ID)

    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        row = c.fetchone()

        if not row:
            c.execute("SELECT * FROM users WHERE LOWER(name) = ?", (email,))
            row = c.fetchone()

        if not row or row["password_hash"] != password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user_id = row["user_id"]
        name = row["name"]
        email_val = row["email"] or email
        role = row["role"] if "role" in row and row["role"] else "customer"
        user_tenant_id = row["tenant_id"] if "tenant_id" in row and row["tenant_id"] else tenant_id

    token = create_token(user_id, email_val, role, user_tenant_id)
    return {
        "token": token,
        "name": name,
        "email": email_val,
        "role": role,
        "avatar": "",
        "tenant_id": user_tenant_id,
    }

@router.post("/register")
def register(req_body: RegisterRequest, req: Request):
    email = req_body.email.strip().lower()
    name = req_body.name.strip()
    phone = req_body.phone.strip() if req_body.phone else ""
    password_hash = hash_password(req_body.password)

    tenant_id = getattr(req.state, "tenant_id", DEFAULT_TENANT_ID)

    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        if c.fetchone():
            raise HTTPException(status_code=400, detail="User with this email already registered")

        user_id = "U" + str(uuid.uuid4().hex[:8]).upper()
        role = "customer"
        c.execute(
            "INSERT INTO users (user_id, name, email, phone, password_hash, role, tenant_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, name, email, phone, password_hash, role, tenant_id),
        )
        logger.info("Registered new user: %s (%s)", name, email)

    token = create_token(user_id, email, role, tenant_id)
    return {
        "token": token,
        "name": name,
        "email": email,
        "role": role,
        "avatar": "",
        "tenant_id": tenant_id,
    }

