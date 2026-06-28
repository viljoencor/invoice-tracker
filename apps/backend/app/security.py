import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

ph = PasswordHasher()
bearer = HTTPBearer(auto_error=True)


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        ph.verify(hashed, password)
        return True
    except Exception:
        return False


def create_access_token(sub: str, org_id: str, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "org_id": org_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


async def get_current_claims(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    token = creds.credentials
    claims = decode_token(token)
    if claims.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return claims


def hash_refresh_token(raw: str) -> str:
    """Return SHA-256 hex digest of a raw refresh token."""
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_refresh_token() -> tuple[str, str]:
    """Return (raw_opaque_token, sha256_hex_hash)."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_refresh_token(raw)


def require_role(*roles: str) -> Any:
    """FastAPI dependency factory: enforce that the authenticated user has one of the given roles."""

    async def _check(claims: dict = Depends(get_current_claims)) -> dict:
        if claims.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return claims

    return _check
