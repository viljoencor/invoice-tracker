import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import engine, get_db
from ..middleware import limiter
from ..models import Invoice, Payment
from ..schemas import PaymentIn
from ..security import get_current_claims, require_role

router = APIRouter(prefix="/payments", tags=["payments"])

# SELECT ... FOR UPDATE is not supported by SQLite; guard against it at runtime
# so that the SQLite-based unit-test suite can still exercise the payment logic.
_USE_ROW_LOCK: bool = engine.dialect.name != "sqlite"


@router.post("")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def apply_payment(
    request: Request,  # noqa: ARG001
    body: PaymentIn,
    claims: dict = Depends(require_role("OWNER")),
    db: AsyncSession = Depends(get_db),
    # fastapi header matching is case-insensitive but being safe here
    idemp_std: str | None = Header(default=None, alias="Idempotency-Key"),
    idemp_alt: str | None = Header(default=None, alias="idempotency-key"),
):
    # Idempotency key + row lock prevents double-charging when clients retry a failed request.
    # Step 1: Require idempotency key;
    # Step 2: Pre-check for duplicate;
    # Step 3: Lock invoice row (Postgres only);
    # Step 4: Re-check inside lock;
    # Step 5: Validate amount;
    # Step 6: Insert payment + deduct balance + update status;
    # Step 7: Handle race via unique constraint fallback.
    org_id = claims["org_id"]
    x_idempotency_key = idemp_std or idemp_alt
    if not x_idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

    # Fast pre-check: return early for clearly duplicate keys (non-concurrent path)
    existing = await db.scalar(
        select(Payment).where(
            Payment.org_id == org_id,
            Payment.idempotency_key == x_idempotency_key,
        )
    )
    if existing:
        return {"status": "ok", "payment_id": str(existing.id), "note": "idempotent-return"}

    # Lock the invoice row before any balance read/write.
    # SELECT ... FOR UPDATE is skipped on SQLite (no row-level locking; the
    # unit tests cover the logical checks, while the PostgreSQL integration
    # tests in test_payments_pg.py cover the locking semantics).
    inv_q = select(Invoice).where(Invoice.id == body.invoice_id, Invoice.org_id == org_id)
    if _USE_ROW_LOCK:
        inv_q = inv_q.with_for_update()
    inv = await db.scalar(inv_q)

    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Re-check idempotency inside the lock: a concurrent request with the same
    # key may have committed between our pre-check and the lock acquisition.
    existing = await db.scalar(
        select(Payment).where(
            Payment.org_id == org_id,
            Payment.idempotency_key == x_idempotency_key,
        )
    )
    if existing:
        return {"status": "ok", "payment_id": str(existing.id), "note": "idempotent-return"}

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

    # Deduct balance and mark status atomically with the payment insert
    inv.balance_cents = inv.balance_cents - body.amount_cents
    inv.status = "paid" if inv.balance_cents == 0 else "partially_paid"

    try:
        await db.commit()
    except IntegrityError:
        # Two requests with the same idempotency key raced past both checks
        # (only possible when they target different invoices or on non-locking
        # dialects).  The unique constraint fires; return the winning record.
        await db.rollback()
        existing_after_conflict = await db.scalar(
            select(Payment).where(
                Payment.org_id == org_id,
                Payment.idempotency_key == x_idempotency_key,
            )
        )
        if existing_after_conflict:
            return {
                "status": "ok",
                "payment_id": str(existing_after_conflict.id),
                "note": "idempotent-return",
            }
        raise HTTPException(status_code=409, detail="Payment conflict") from None

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
    # Returns payment history scoped to one invoice so the detail view can show a full audit trail.
    # Step 1: Verify invoice belongs to org;
    # Step 2: Return payments ordered newest-first.
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
