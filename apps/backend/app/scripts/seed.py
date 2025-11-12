import asyncio
from datetime import date, timedelta

from argon2 import PasswordHasher

from app.db import async_session_maker
from app.models import Client, Invoice, InvoiceItem, InvoiceSeq, Org, OrgMember, User

ph = PasswordHasher()


async def run():
    async with async_session_maker() as db:  # type: AsyncSession
        org = Org(name="Demo Org")
        user = User(email="admin@example.com", name="Admin", password_hash=ph.hash("admin123"))
        db.add_all([org, user])
        await db.flush()
        db.add(OrgMember(org_id=org.id, user_id=user.id, role="OWNER"))
        db.add(InvoiceSeq(org_id=org.id, next_seq=1))

        c1 = Client(org_id=org.id, name="Acme Pty Ltd", email="billing@acme.co.za")
        db.add(c1)
        await db.flush()

        inv = Invoice(
            org_id=org.id,
            client_id=c1.id,
            number="INV-2025-00001",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            currency="ZAR",
            subtotal_cents=100000,
            tax_cents=15000,
            total_cents=115000,
            balance_cents=115000,
            status="DRAFT",
            notes="Seeded invoice",
        )
        db.add(inv)
        await db.flush()

        db.add_all(
            [
                InvoiceItem(
                    invoice_id=inv.id,
                    line_no=1,
                    description="Consulting hours",
                    qty=10,
                    unit_price_cents=10000,
                    tax_rate_bp=1500,
                    line_total_cents=115000,
                ),
            ]
        )
        await db.commit()
        print("Seeded org, user, client, and invoice. Email: admin@example.com / admin123")


if __name__ == "__main__":
    asyncio.run(run())
