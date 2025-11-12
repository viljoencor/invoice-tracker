from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import async_session_maker
from ..models import Client
from ..schemas import ClientIn, ClientOut
from ..security import get_current_claims

router = APIRouter(prefix="/clients", tags=["clients"])


async def get_db():
    async with async_session_maker() as s:
        yield s


@router.post("", response_model=ClientOut)
async def create_client(
    body: ClientIn, claims=Depends(get_current_claims), db: AsyncSession = Depends(get_db)
):
    org_id = claims["org_id"]
    c = Client(
        org_id=org_id, name=body.name, email=body.email, billing_address=body.billing_address
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@router.get("", response_model=list[ClientOut])
async def list_clients(
    q: str | None = Query(default=None),  # noqa: ARG001
    claims=Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Client).where(Client.org_id == claims["org_id"]).order_by(Client.created_at.desc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())
