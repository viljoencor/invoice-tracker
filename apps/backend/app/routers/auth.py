import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import async_session_maker
from ..models import User, Org, OrgMember
from ..schemas import RegisterRequest, LoginRequest, TokenPair
from ..security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

async def get_db():
    async with async_session_maker() as s:
        yield s

@router.post("/register", response_model=TokenPair)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
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
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
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