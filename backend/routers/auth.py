"""
MediTwin AI — Authentication Router
Uses Python built-in hashlib (no passlib/bcrypt dependency).
Persists users to SQLite (db.py) — survives restarts, no external DB needed.
"""
from __future__ import annotations
import hashlib, os, secrets
from datetime import UTC, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from models.schemas import TokenResponse, UserLogin, UserRegister
import db

router   = APIRouter()
security = HTTPBearer()

SECRET_KEY  = os.getenv("SECRET_KEY", "meditwin-change-this-secret-in-production-32ch")
ALGORITHM   = os.getenv("ALGORITHM", "HS256")
EXPIRE_MINS = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def hash_password(password: str) -> str:
    """PBKDF2-SHA256 with random salt — secure, no external deps."""
    salt = secrets.token_hex(16)
    h    = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"{salt}${h.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    try:
        salt, h = stored.split("$", 1)
        new_h   = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 260_000)
        return secrets.compare_digest(new_h.hex(), h)
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + timedelta(minutes=EXPIRE_MINS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token",
                            headers={"WWW-Authenticate": "Bearer"}) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    return decode_token(credentials.credentials)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserRegister) -> TokenResponse:
    if db.get_user_by_email(body.email):
        raise HTTPException(400, "Email already registered")
    uid = f"USR-{db.count_users()+1:05d}"
    db.create_user(
        user_id=uid, name=body.name, email=body.email,
        hashed_password=hash_password(body.password), role=body.role,
    )
    token = create_access_token({"sub": body.email, "user_id": uid, "role": body.role})
    return TokenResponse(access_token=token, expires_in=EXPIRE_MINS*60, user_id=uid, role=body.role)


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin) -> TokenResponse:
    user = db.get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token = create_access_token({"sub": body.email, "user_id": user["id"], "role": user["role"]})
    return TokenResponse(access_token=token, expires_in=EXPIRE_MINS*60, user_id=user["id"], role=user["role"])


@router.get("/me")
async def me(user: dict = Depends(get_current_user)) -> dict:
    return {"user_id": user.get("user_id"), "email": user.get("sub"), "role": user.get("role")}


@router.post("/refresh")
async def refresh(user: dict = Depends(get_current_user)) -> dict:
    token = create_access_token({"sub": user["sub"], "user_id": user["user_id"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer", "expires_in": EXPIRE_MINS * 60}
