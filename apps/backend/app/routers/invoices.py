# app/routers/invoices.py
import uuid
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy import desc, func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_db
from ..middleware import limiter
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
    # Round Decimal to nearest integer cent using ROUND_HALF_UP.
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
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def create_invoice(
    request: Request,  # noqa: ARG001
    body: InvoiceCreate,
    claims: dict = Depends(require_role("OWNER")),
    db: AsyncSession = Depends(get_db),
    idemp_std: str | None = Header(default=None, alias="Idempotency-Key"),
    idemp_alt: str | None = Header(default=None, alias="idempotency-key"),
):
    # Idempotency key mirrors the payments endpoint: a network retry or double-click on submit
    # must return the original invoice, never silently create a duplicate billing document.
    # Step 1: Require idempotency key;
    # Step 2: Return existing invoice if the key was already used;
    # Step 3: Verify client belongs to org;
    # Step 4: Compute totals;
    # Step 5: Get atomic sequence number;
    # Step 6: Persist invoice + line items (unique-constraint fallback handles races);
    # Step 7: Return InvoiceOut.
    org_id: uuid.UUID = claims["org_id"]
    idempotency_key = idemp_std or idemp_alt
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

    existing = await db.scalar(
        select(Invoice).where(Invoice.org_id == org_id, Invoice.idempotency_key == idempotency_key)
    )
    if existing:
        return InvoiceOut(
            id=existing.id,
            number=existing.number,
            client_id=existing.client_id,
            issue_date=existing.issue_date,
            due_date=existing.due_date,
            currency=existing.currency,
            subtotal_cents=existing.subtotal_cents,
            tax_cents=existing.tax_cents,
            total_cents=existing.total_cents,
            balance_cents=existing.balance_cents,
            status=existing.status,
        )

    client = await db.scalar(
        select(Client.id).where(
            Client.id == body.client_id,
            Client.org_id == org_id,
            Client.deleted_at.is_(None),
        )
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
        idempotency_key=idempotency_key,
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
        if "uq_invoices_org_idem" in str(e.orig):
            # Two requests with the same idempotency key raced past the pre-check.
            existing_after_conflict = await db.scalar(
                select(Invoice).where(
                    Invoice.org_id == org_id, Invoice.idempotency_key == idempotency_key
                )
            )
            if existing_after_conflict:
                return InvoiceOut(
                    id=existing_after_conflict.id,
                    number=existing_after_conflict.number,
                    client_id=existing_after_conflict.client_id,
                    issue_date=existing_after_conflict.issue_date,
                    due_date=existing_after_conflict.due_date,
                    currency=existing_after_conflict.currency,
                    subtotal_cents=existing_after_conflict.subtotal_cents,
                    tax_cents=existing_after_conflict.tax_cents,
                    total_cents=existing_after_conflict.total_cents,
                    balance_cents=existing_after_conflict.balance_cents,
                    status=existing_after_conflict.status,
                )
            raise HTTPException(status_code=409, detail="Invoice conflict") from None
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
    # Aggregates all billing KPIs in one pass so the dashboard loads with a single API call.
    # Step 1: Query total due, overdue count, paid-last-30d, upcoming due;
    # Step 2: Rollup 12-month revenue;
    # Step 3: Return combined summary.
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
    # Joins client name into the result so the detail view doesn't need a second request.
    # Step 1: JOIN invoice with client;
    # Step 2: Scope to org;
    # Step 3: Return InvoiceDetail with client_name.
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
    # Generates the PDF on demand from live data so it always reflects the current balance.
    # Step 1: Load invoice + client + items scoped to org; Step 2: Render PDF via ReportLab; Step 3: Return as application/pdf.
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
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    claims=Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
):
    # Supports sort/filter/pagination so large orgs don't have to load all invoices at once.
    # Step 1: Scope to org; Step 2: Apply status/client filters; Step 3: Sort and paginate; Step 4: Return InvoiceList rows.
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
    # Status guard (draft→sent only) prevents accidentally re-sending a paid or overdue invoice.
    # Step 1: UPDATE status draft→sent scoped to org; Step 2: Raise 400 if no row matched.
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
