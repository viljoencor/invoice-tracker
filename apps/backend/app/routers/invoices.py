# app/routers/invoices.py
import uuid
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc, func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Client, Invoice, InvoiceItem
from ..schemas import (
    InvoiceCreate,
    InvoiceDetail,  # <-- include detail schema
    InvoiceList,
    InvoiceOut,
    InvoiceSummary,
)
from ..security import get_current_claims, require_role
from ..services.pdf import render_invoice_pdf

router = APIRouter(prefix="/invoices", tags=["invoices"])

ALLOWED_SORTS = {
    "issue_date": Invoice.issue_date,
    "due_date": Invoice.due_date,
    "number": Invoice.number,
    "total_cents": Invoice.total_cents,
    "balance_cents": Invoice.balance_cents,
    "status": Invoice.status,
}


def _bp_to_fraction(bp: int) -> Decimal:
    # basis points to decimal (1500 bp = 0.15 = 15%)
    return (Decimal(bp) / Decimal(10000)).quantize(Decimal("0.0001"))


def _to_cents(x: Decimal) -> int:
    return int(x.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calc_totals(items: list) -> tuple[int, int, int]:
    # Accumulate in Decimal then round once per bucket to avoid floating-point drift
    subtotal = Decimal(0)
    tax = Decimal(0)
    for it in items:
        qty = Decimal(str(it.qty))
        unit = Decimal(it.unit_price_cents)
        line_sub = qty * unit
        line_tax = line_sub * _bp_to_fraction(it.tax_rate_bp)
        subtotal += line_sub
        tax += line_tax
    subtotal_cents = _to_cents(subtotal)
    tax_cents = _to_cents(tax)
    total_cents = subtotal_cents + tax_cents
    return subtotal_cents, tax_cents, total_cents


async def next_invoice_number(db: AsyncSession, org_id: uuid.UUID, year: int) -> str:
    # INSERT ... ON CONFLICT DO UPDATE ... RETURNING is a single atomic operation;
    # PostgreSQL guarantees next_seq increments exactly once per call with no race.
    sql = text(
        """
        INSERT INTO invoice_seq (org_id, next_seq)
        VALUES (:org_id, 1)
        ON CONFLICT (org_id)
        DO UPDATE SET next_seq = invoice_seq.next_seq + 1
        RETURNING next_seq
        """
    )
    row = (await db.execute(sql, {"org_id": org_id})).first()
    next_seq = int(row[0])  # type: ignore[index]
    return f"INV-{year}-{next_seq:05d}"


@router.post("", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    body: InvoiceCreate,
    claims: dict = Depends(require_role("OWNER")),
    db: AsyncSession = Depends(get_db),
):
    org_id: uuid.UUID = claims["org_id"]

    client = await db.scalar(
        select(Client.id).where(Client.id == body.client_id, Client.org_id == org_id)
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    subtotal, tax, total = calc_totals(body.items)
    number = await next_invoice_number(db, org_id, body.issue_date.year)

    inv = Invoice(
        id=uuid.uuid4(),
        org_id=org_id,
        client_id=body.client_id,
        number=number,
        issue_date=body.issue_date,
        due_date=body.due_date,
        currency=body.currency,
        subtotal_cents=subtotal,
        tax_cents=tax,
        total_cents=total,
        balance_cents=total,
        status="draft",  # lower-case to match filters
        notes=body.notes,
        meta={},
    )
    db.add(inv)

    for i, it in enumerate(body.items, start=1):
        qty = Decimal(str(it.qty))
        unit = Decimal(it.unit_price_cents)
        line_total = _to_cents(qty * unit * (Decimal(1) + _bp_to_fraction(it.tax_rate_bp)))
        db.add(
            InvoiceItem(
                invoice_id=inv.id,
                line_no=i,
                description=it.description,
                qty=float(qty),
                unit_price_cents=int(unit),
                tax_rate_bp=it.tax_rate_bp,
                line_total_cents=line_total,
            )
        )

    try:
        await db.flush()
        await db.commit()
        # await db.refresh(inv)  # not needed since we return manually
    except IntegrityError as e:
        await db.rollback()
        if "uq_invoices_org_number" in str(e.orig):
            raise HTTPException(
                status_code=409, detail=f"Invoice number already exists: {number}"
            ) from e
        raise

    return InvoiceOut(
        id=inv.id,
        number=inv.number,
        client_id=inv.client_id,
        issue_date=inv.issue_date,
        due_date=inv.due_date,
        currency=inv.currency,
        subtotal_cents=inv.subtotal_cents,
        tax_cents=inv.tax_cents,
        total_cents=inv.total_cents,
        balance_cents=inv.balance_cents,
        status=inv.status,
    )


@router.get("/summary", response_model=InvoiceSummary)
async def get_invoice_summary(
    claims=Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
):
    org_id = claims["org_id"]
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    total_due_res = await db.execute(
        select(func.coalesce(func.sum(Invoice.balance_cents), 0)).where(
            Invoice.org_id == org_id,
            Invoice.status.in_(["draft", "sent", "overdue"]),
        )
    )
    total_due_cents = int(total_due_res.scalar() or 0)

    overdue_res = await db.execute(
        select(func.count()).where(
            Invoice.org_id == org_id,
            Invoice.status == "overdue",
        )
    )
    overdue_count = int(overdue_res.scalar() or 0)

    # This query might be slow with lots of invoices - consider caching
    paid_last_30d_res = await db.execute(
        select(func.coalesce(func.sum(Invoice.total_cents - Invoice.balance_cents), 0)).where(
            Invoice.org_id == org_id,
            Invoice.status == "paid",
            Invoice.due_date >= thirty_days_ago,
        )
    )
    paid_last_30d_cents = int(paid_last_30d_res.scalar() or 0)

    upcoming_due_res = await db.execute(
        select(func.coalesce(func.sum(Invoice.balance_cents), 0)).where(
            Invoice.org_id == org_id,
            Invoice.status.in_(["draft", "sent"]),
            Invoice.due_date > today,
        )
    )
    upcoming_due_cents = int(upcoming_due_res.scalar() or 0)

    twelve_months_ago = today - timedelta(days=365)  # close enough
    # using raw SQL here because SQLAlchemy date_trunc was giving me headaches
    revenue_query = text(
        """
        SELECT date_trunc('month', issue_date) AS month,
            sum(total_cents) AS total_cents,
            count(*) AS count
        FROM invoices
        WHERE org_id = :org_id
          AND issue_date >= :start_date
        GROUP BY date_trunc('month', issue_date)
        ORDER BY month DESC
        """
    )
    rev_rows = (
        (await db.execute(revenue_query, {"org_id": org_id, "start_date": twelve_months_ago}))
        .mappings()
        .all()
    )
    revenue_by_month = [
        {
            "month": r["month"].strftime("%Y-%m"),
            "total_cents": int(r["total_cents"] or 0),
            "count": int(r["count"] or 0),
        }
        for r in rev_rows
    ]

    return {
        "total_due_cents": total_due_cents,
        "overdue_count": overdue_count,
        "paid_last_30d_cents": paid_last_30d_cents,
        "upcoming_due_cents": upcoming_due_cents,
        "revenue_by_month": revenue_by_month,
    }


@router.get("/{invoice_id}", response_model=InvoiceDetail)
async def get_invoice(
    invoice_id: uuid.UUID,
    claims=Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            Invoice.id.label("id"),
            Invoice.number.label("number"),
            Invoice.client_id.label("client_id"),
            Invoice.issue_date.label("issue_date"),
            Invoice.due_date.label("due_date"),
            Invoice.currency.label("currency"),
            Invoice.subtotal_cents.label("subtotal_cents"),
            Invoice.tax_cents.label("tax_cents"),
            Invoice.total_cents.label("total_cents"),
            Invoice.balance_cents.label("balance_cents"),
            Invoice.status.label("status"),
            Client.name.label("client_name"),  # for UI
        )
        .join(Client, Client.id == Invoice.client_id)
        .where(Invoice.id == invoice_id, Invoice.org_id == claims["org_id"])
        .limit(1)
    )

    row = (await db.execute(stmt)).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceDetail(**row)


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: uuid.UUID,
    claims=Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
):
    inv = await db.scalar(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.org_id == claims["org_id"])
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    client = await db.scalar(select(Client).where(Client.id == inv.client_id))
    items = (
        (await db.execute(select(InvoiceItem).where(InvoiceItem.invoice_id == inv.id)))
        .scalars()
        .all()
    )

    payload = render_invoice_pdf(
        invoice={
            "number": inv.number,
            "issue_date": inv.issue_date,
            "due_date": inv.due_date,
            "subtotal_cents": inv.subtotal_cents,
            "tax_cents": inv.tax_cents,
            "total_cents": inv.total_cents,
            "balance_cents": inv.balance_cents,
        },
        client={"name": client.name, "email": client.email},  # type: ignore[union-attr]
        items=[
            {
                "description": it.description,
                "qty": float(it.qty),
                "unit_price_cents": it.unit_price_cents,
                "line_total_cents": it.line_total_cents,
            }
            for it in items
        ],
    )
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=invoice-{inv.number}.pdf"},
    )


@router.get("", response_model=list[InvoiceList])
async def list_invoices(
    status: str | None = None,
    client_id: uuid.UUID | None = None,
    sort: str = "-issue_date",
    limit: int = Query(50, le=10000),
    offset: int = Query(0, ge=0),
    claims=Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
):
    sort_key = sort.lstrip("-")
    sort_col = ALLOWED_SORTS.get(sort_key, Invoice.issue_date)
    order_by = desc(sort_col) if sort.startswith("-") else sort_col

    stmt = (
        select(
            Invoice.id.label("id"),
            Invoice.number.label("number"),
            Client.name.label("client_name"),
            Invoice.issue_date.label("issue_date"),
            Invoice.due_date.label("due_date"),
            Invoice.total_cents.label("total_cents"),
            Invoice.balance_cents.label("balance_cents"),
            Invoice.status.label("status"),
            Invoice.currency.label("currency"),
        )
        .join(Client, Client.id == Invoice.client_id)
        .where(Invoice.org_id == claims["org_id"])
    )

    if status:
        stmt = stmt.where(Invoice.status == status)
    if client_id:
        stmt = stmt.where(Invoice.client_id == client_id)

    stmt = stmt.order_by(order_by).offset(offset).limit(limit)

    rows = (await db.execute(stmt)).mappings().all()
    return [InvoiceList(**row) for row in rows]


@router.post("/{invoice_id}/send")
async def mark_invoice_sent(
    invoice_id: uuid.UUID,
    claims: dict = Depends(require_role("OWNER")),
    db: AsyncSession = Depends(get_db),
):
    org_id = claims["org_id"]
    stmt = (
        update(Invoice)
        .where(Invoice.id == invoice_id, Invoice.org_id == org_id, Invoice.status == "draft")
        .values(status="sent")
        .returning(
            Invoice.id, Invoice.number, Invoice.status, Invoice.balance_cents, Invoice.total_cents
        )
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=400, detail="Invoice not found or not in draft")
    await db.commit()
    return {"status": "ok", "invoice_id": str(row.id), "invoice_status": row.status}
