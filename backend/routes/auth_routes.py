import uuid
import base64
import json
import logging
import hashlib
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db import get_conn

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
def google_auth(req: GoogleAuthRequest):
    payload = decode_google_credential(req.credential)
    email = payload.get("email")
    name = payload.get("name", "Google User")
    avatar = payload.get("picture", "")

    if not email:
        raise HTTPException(status_code=400, detail="Google authentication did not provide email")

    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = c.fetchone()

        if row:
            user_id = row["user_id"]
            name = row["name"]
        else:
            user_id = "U" + str(uuid.uuid4().hex[:8]).upper()
            c.execute(
                "INSERT INTO users (user_id, name, email, phone, password_hash) VALUES (?, ?, ?, ?, ?)",
                (user_id, name, email, "", ""),
            )
            logger.info("Created new user via Google Sign-In: %s (%s)", name, email)

    # Return JWT token (mock) and profile details
    return {
        "token": f"mock-google-token-{user_id}",
        "name": name,
        "email": email,
        "role": "user",
        "avatar": avatar,
    }

@router.post("/login")
def login(req: LoginRequest):
    email = req.email.strip().lower()
    password_hash = hash_password(req.password)

    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        row = c.fetchone()

        if not row:
            # Check username match if username was stored in name column
            c.execute("SELECT * FROM users WHERE LOWER(name) = ?", (email,))
            row = c.fetchone()

        if not row or row["password_hash"] != password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user_id = row["user_id"]
        name = row["name"]
        email_val = row["email"] or email

    return {
        "token": f"mock-login-token-{user_id}",
        "name": name,
        "email": email_val,
        "role": "user",
        "avatar": "",
    }

@router.post("/register")
def register(req: RegisterRequest):
    email = req.email.strip().lower()
    name = req.name.strip()
    phone = req.phone.strip() if req.phone else ""
    password_hash = hash_password(req.password)

    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        if c.fetchone():
            raise HTTPException(status_code=400, detail="User with this email already registered")

        user_id = "U" + str(uuid.uuid4().hex[:8]).upper()
        c.execute(
            "INSERT INTO users (user_id, name, email, phone, password_hash) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, email, phone, password_hash),
        )
        logger.info("Registered new user: %s (%s)", name, email)

    return {
        "token": f"mock-register-token-{user_id}",
        "name": name,
        "email": email,
        "role": "user",
        "avatar": "",
    }
