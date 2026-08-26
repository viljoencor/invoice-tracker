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
    # Argon2id is GPU-resistant and OWASP-recommended for password storage.
    # Step 1: Hash plain-text password with Argon2id; returns opaque hash string.
    return ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    # Returns False instead of raising so callers can issue a uniform 401 without leaking which field failed.
    # Step 1: Re-verify candidate against stored Argon2 hash;
    # Step 2: Return False on any mismatch.
    try:
        ph.verify(hashed, password)
        return True
    except Exception:
        return False


def create_access_token(sub: str, org_id: str, role: str) -> str:
    # Short-lived JWT (30 min) limits exposure if intercepted; role+org embedded to avoid DB lookups per request.
    # Step 1: Build payload (sub, org_id, role, iat, exp);
    # Step 2: Sign with HS256; returns JWT string.
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
    # Centralised decode so every route automatically inherits signature and expiry validation.
    # Step 1: Verify signature and expiry;
    # Step 2: Return claims dict; raises 401 on any JWT error.
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


async def get_current_claims(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    # FastAPI dependency that converts a raw Bearer token into validated claims for any protected route.
    # Step 1: Extract Bearer token;
    # Step 2: Decode JWT;
    # Step 3: Reject non-access token types; returns claims.
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
        # Blocks the route before any business logic runs if the caller's role is not in the allowed set.
        # Step 1: Read role from JWT claims;
        # Step 2: Raise 403 if not in allowed roles; returns claims.
        if claims.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return claims

    return _check
