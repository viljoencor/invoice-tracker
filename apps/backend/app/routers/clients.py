import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Client
from ..schemas import ClientIn, ClientOut, ClientUpdate
from ..security import get_current_claims, require_role

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: ClientIn,
    claims: dict = Depends(require_role("OWNER")),
    db: AsyncSession = Depends(get_db),
):
    # Only OWNER role can add clients to prevent members from modifying billing contacts.
    # Step 1: Require OWNER role;
    # Step 2: Persist new client under caller's org;
    # Step 3: Return refreshed row.
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
    # Supports name/email search so the invoice form can find clients without loading all of them.
    # Step 1: Scope to org;
    # Step 2: Apply optional case-insensitive name/email LIKE filter;
    # Step 3: Order newest-first.
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
    # Scoped to org_id so users can never read another organisation's clients.
    # Step 1: Fetch client scoped to org;
    # Step 2: Raise 404 if not found.
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
    # PATCH so the frontend only needs to send changed fields, not the full record.
    # Step 1: Fetch client scoped to org;
    # Step 2: Apply partial field update;
    # Step 3: Commit and return refreshed row.
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
    # The 409 guard prevents orphaned invoices referencing a deleted client.
    # Step 1: Fetch client scoped to org;
    # Step 2: Delete;
    # Step 3: Rollback and raise 409 if FK constraint fires.
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
