import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_db
from ..middleware import limiter
from ..models import Org, OrgMember, RefreshToken, User
from ..schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenPair, UserOut
from ..security import (
    create_access_token,
    generate_refresh_token,
    get_current_claims,
    hash_password,
    hash_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def register(request: Request, body: RegisterRequest, db: AsyncSession = Depends(get_db)):  # noqa: ARG001
    q = await db.execute(select(User).where(User.email == body.email))
    if q.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    org = Org(name=f"{body.name.split()[0]}'s Org")
    user = User(email=body.email, name=body.name, password_hash=hash_password(body.password))
    db.add_all([org, user])
    await db.flush()
    db.add(OrgMember(org_id=org.id, user_id=user.id, role="OWNER"))
    await db.flush()

    raw_refresh, token_hash = generate_refresh_token()
    expires = datetime.now(UTC) + timedelta(minutes=settings.refresh_token_expire_minutes)
    db.add(RefreshToken(token_hash=token_hash, user_id=user.id, org_id=org.id, expires_at=expires))
    await db.commit()

    access = create_access_token(str(user.id), str(org.id), "OWNER")
    return TokenPair(access_token=access, refresh_token=raw_refresh)


@router.post("/login", response_model=TokenPair)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):  # noqa: ARG001
    q = await db.execute(select(User).where(User.email == body.email))
    user = q.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    oq = await db.execute(
        select(OrgMember.org_id, OrgMember.role).where(OrgMember.user_id == user.id)
    )
    row = oq.first()
    if not row:
        raise HTTPException(status_code=403, detail="User not in any org")

    org_id, role = row[0], row[1]

    raw_refresh, token_hash = generate_refresh_token()
    expires = datetime.now(UTC) + timedelta(minutes=settings.refresh_token_expire_minutes)
    db.add(RefreshToken(token_hash=token_hash, user_id=user.id, org_id=org_id, expires_at=expires))
    await db.commit()

    access = create_access_token(str(user.id), str(org_id), role)
    return TokenPair(access_token=access, refresh_token=raw_refresh)


@router.get("/me", response_model=UserOut)
async def get_me(claims: dict = Depends(get_current_claims), db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == claims["sub"]))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    membership = (
        await db.execute(
            select(OrgMember).where(
                OrgMember.user_id == claims["sub"],
                OrgMember.org_id == claims["org_id"],
            )
        )
    ).scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organisation")

    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        org_id=uuid.UUID(claims["org_id"]),
        role=membership.role,
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    now = datetime.now(UTC)
    token_hash = hash_refresh_token(body.refresh_token)

    rt = (
        await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    ).scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Normalise expiry for SQLite (stored as TZ-naive)
    expires = rt.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)

    if rt.revoked or expires <= now:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    membership = (
        await db.execute(
            select(OrgMember).where(
                OrgMember.user_id == rt.user_id,
                OrgMember.org_id == rt.org_id,
            )
        )
    ).scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Rotate: revoke the used token, issue a replacement
    rt.revoked = True
    raw_new, hash_new = generate_refresh_token()
    new_expires = now + timedelta(minutes=settings.refresh_token_expire_minutes)
    db.add(
        RefreshToken(
            token_hash=hash_new,
            user_id=rt.user_id,
            org_id=rt.org_id,
            expires_at=new_expires,
        )
    )
    await db.commit()

    access = create_access_token(str(rt.user_id), str(rt.org_id), membership.role)
    return TokenPair(access_token=access, refresh_token=raw_new)


@router.post("/logout", status_code=204)
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Revoke the supplied refresh token. Already-issued access tokens remain valid until expiry."""
    token_hash = hash_refresh_token(body.refresh_token)
    await db.execute(
        update(RefreshToken).where(RefreshToken.token_hash == token_hash).values(revoked=True)
    )
    await db.commit()
    return None
