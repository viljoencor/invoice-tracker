# app/routers/dash.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import async_session_maker
from ..security import get_current_claims

router = APIRouter(prefix="/dash", tags=["dashboard"])

async def get_db():
    async with async_session_maker() as s:
        yield s

@router.get("/summary")
async def summary(claims=Depends(get_current_claims), db: AsyncSession = Depends(get_db)):
    org_id = claims["org_id"]

    sql = text("""
        WITH base AS (
            SELECT total_cents, balance_cents,
                   GREATEST(0, (CURRENT_DATE - due_date))::int AS days_overdue
            FROM invoices
            WHERE org_id = :org AND LOWER(status) <> 'void'
        )
        SELECT
            COALESCE((SELECT SUM(total_cents)   FROM invoices WHERE org_id=:org), 0) AS total_billed_cents,
            COALESCE((SELECT SUM(balance_cents) FROM invoices WHERE org_id=:org), 0) AS total_due_cents,
            COALESCE((SELECT COUNT(*) FROM invoices WHERE org_id=:org AND balance_cents>0 AND due_date<CURRENT_DATE), 0) AS overdue_count,
            -- Pending = positive balance AND status is draft/sent/partially_paid
            COALESCE((
                SELECT COUNT(*)
                FROM invoices
                WHERE org_id=:org
                  AND balance_cents > 0
                  AND LOWER(status) IN ('draft','sent','partially_paid')
            ), 0) AS pending_count,
            SUM(balance_cents) FILTER (WHERE days_overdue BETWEEN 0 AND 30)  AS bkt_0_30,
            SUM(balance_cents) FILTER (WHERE days_overdue BETWEEN 31 AND 60) AS bkt_31_60,
            SUM(balance_cents) FILTER (WHERE days_overdue BETWEEN 61 AND 90) AS bkt_61_90,
            SUM(balance_cents) FILTER (WHERE days_overdue > 90)              AS bkt_90p
        FROM base;
    """)
    kpis = (await db.execute(sql, {"org": org_id})).mappings().first() or {}

    rev_sql = text("""
        SELECT date_trunc('month', issue_date) AS month,
               SUM(total_cents) AS total_cents,
               COUNT(*)         AS count
        FROM invoices
        WHERE org_id = :org
          AND issue_date >= (current_date - INTERVAL '365 days')
        GROUP BY 1
        ORDER BY 1 ASC
    """)
    rev_rows = (await db.execute(rev_sql, {"org": org_id})).mappings().all()
    revenue_by_month = [
        {
            "month": r["month"].strftime("%Y-%m"),
            "total_cents": int(r["total_cents"] or 0),
            "count": int(r["count"] or 0),
        }
        for r in rev_rows
    ]

    return { **kpis, "revenue_by_month": revenue_by_month }
