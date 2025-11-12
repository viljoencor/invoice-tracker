from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import async_session_maker
from ..middleware import limiter
from ..models import Org, OrgMember, User
from ..schemas import LoginRequest, RegisterRequest, TokenPair
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_db():
    async with async_session_maker() as s:
        yield s


@router.post("/register", response_model=TokenPair)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def register(request: Request, body: RegisterRequest, db: AsyncSession = Depends(get_db)):  # noqa: ARG001
    # create org + user + membership
    q = await db.execute(select(User).where(User.email == body.email))
    if q.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    org = Org(name=f"{body.name.split()[0]}'s Org")
    user = User(email=body.email, name=body.name, password_hash=hash_password(body.password))
    db.add_all([org, user])
    await db.flush()
    db.add(OrgMember(org_id=org.id, user_id=user.id, role="OWNER"))
    await db.commit()

    access = create_access_token(str(user.id), str(org.id))
    return TokenPair(access_token=access)


@router.post("/login", response_model=TokenPair)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):  # noqa: ARG001
    q = await db.execute(select(User).where(User.email == body.email))
    user = q.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # pick first org (demo)
    oq = await db.execute(select(OrgMember.org_id).where(OrgMember.user_id == user.id))
    row = oq.first()
    if not row:
        raise HTTPException(status_code=403, detail="User not in any org")

    access = create_access_token(str(user.id), str(row[0]))
    return TokenPair(access_token=access)
