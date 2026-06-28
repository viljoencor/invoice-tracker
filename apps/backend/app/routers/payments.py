import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Invoice, Payment
from ..schemas import PaymentIn
from ..security import get_current_claims, require_role

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("")
async def apply_payment(
    body: PaymentIn,
    claims: dict = Depends(require_role("OWNER")),
    db: AsyncSession = Depends(get_db),
    # fastapi header matching is case-insensitive but being safe here
    idemp_std: str | None = Header(default=None, alias="Idempotency-Key"),
    idemp_alt: str | None = Header(default=None, alias="idempotency-key"),
):
    org_id = claims["org_id"]
    x_idempotency_key = idemp_std or idemp_alt
    if not x_idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

    existing = (
        await db.execute(
            select(Payment).where(
                Payment.org_id == org_id,
                Payment.idempotency_key == x_idempotency_key,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return {"status": "ok", "payment_id": str(existing.id), "note": "idempotent-return"}

    inv = (
        await db.execute(
            select(Invoice).where(
                Invoice.id == body.invoice_id,
                Invoice.org_id == org_id,
            )
        )
    ).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    # NOTE: statuses are lowercase elsewhere but checking uppercase here just in case
    if inv.status in ("void", "paid", "VOID", "PAID"):
        raise HTTPException(status_code=400, detail="Cannot apply payment to void/paid invoice")
    if body.amount_cents <= 0 or body.amount_cents > inv.balance_cents:
        raise HTTPException(status_code=400, detail="Invalid payment amount")

    pay = Payment(
        org_id=org_id,
        invoice_id=inv.id,
        amount_cents=body.amount_cents,
        received_at=body.received_at,
        method=body.method,
        reference=body.reference,
        idempotency_key=x_idempotency_key,
    )
    db.add(pay)

    # update balance
    inv.balance_cents = inv.balance_cents - body.amount_cents
    inv.status = "paid" if inv.balance_cents == 0 else "partially_paid"

    await db.commit()
    return {
        "status": "ok",
        "payment_id": str(pay.id),
        "invoice_status": inv.status,
        "balance_cents": inv.balance_cents,
    }


@router.get("")
async def list_payments(
    invoice_id: uuid.UUID,
    claims=Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
):
    org_id = claims["org_id"]
    inv = (
        await db.execute(
            select(Invoice.id).where(Invoice.id == invoice_id, Invoice.org_id == org_id)
        )
    ).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    rows = (
        (
            await db.execute(
                select(Payment)
                .where(Payment.invoice_id == invoice_id)
                .order_by(desc(Payment.created_at))
            )
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": str(p.id),
            "amount_cents": p.amount_cents,
            "received_at": p.received_at,
            "method": p.method,
            "reference": p.reference,
        }
        for p in rows
    ]
