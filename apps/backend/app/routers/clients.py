import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Client
from ..schemas import ClientIn, ClientOut, ClientUpdate
from ..security import get_current_claims, require_role

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientOut)
async def create_client(
    body: ClientIn,
    claims: dict = Depends(require_role("OWNER")),
    db: AsyncSession = Depends(get_db),
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
    q: str | None = Query(default=None),
    claims: dict = Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Client).where(Client.org_id == claims["org_id"])
    if q:
        search = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Client.name).like(search),
                func.lower(Client.email).like(search),
            )
        )
    stmt = stmt.order_by(Client.created_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(
    client_id: uuid.UUID,
    claims: dict = Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
):
    c = (
        await db.execute(
            select(Client).where(Client.id == client_id, Client.org_id == claims["org_id"])
        )
    ).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")
    return c


@router.patch("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: uuid.UUID,
    body: ClientUpdate,
    claims: dict = Depends(require_role("OWNER")),
    db: AsyncSession = Depends(get_db),
):
    c = (
        await db.execute(
            select(Client).where(Client.id == client_id, Client.org_id == claims["org_id"])
        )
    ).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(c, field, value)
    await db.commit()
    await db.refresh(c)
    return c


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: uuid.UUID,
    claims: dict = Depends(require_role("OWNER")),
    db: AsyncSession = Depends(get_db),
):
    c = (
        await db.execute(
            select(Client).where(Client.id == client_id, Client.org_id == claims["org_id"])
        )
    ).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")
    try:
        await db.delete(c)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="Client has invoices and cannot be deleted"
        ) from None
    return None
