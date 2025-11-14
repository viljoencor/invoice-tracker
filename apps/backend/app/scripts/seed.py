import asyncio
from datetime import date

from argon2 import PasswordHasher

from app.db import async_session_maker
from app.models import Client, Invoice, InvoiceItem, InvoiceSeq, Org, OrgMember, Payment, User

ph = PasswordHasher()


async def run():
    async with async_session_maker() as db:  # type: AsyncSession
        # Create organization and user
        org = Org(name="Demo Org")
        user = User(email="admin@example.com", name="Admin", password_hash=ph.hash("admin123"))
        db.add_all([org, user])
        await db.flush()
        db.add(OrgMember(org_id=org.id, user_id=user.id, role="OWNER"))
        db.add(InvoiceSeq(org_id=org.id, next_seq=8))  # next available number

        # Create clients
        c1 = Client(org_id=org.id, name="Acme Pty Ltd", email="billing@acme.co.za")
        c2 = Client(org_id=org.id, name="Cor Viljoen", email="billing@cor.co.za")
        c3 = Client(org_id=org.id, name="007 Pty Ltd", email="billing@007.co.za")
        db.add_all([c1, c2, c3])
        await db.flush()

        # Create invoices
        inv1 = Invoice(
            org_id=org.id,
            client_id=c1.id,
            number="INV-2025-00001",
            issue_date=date(2025, 10, 31),
            due_date=date(2025, 11, 30),
            currency="ZAR",
            subtotal_cents=100000,
            tax_cents=15000,
            total_cents=115000,
            balance_cents=115000,
            status="draft",
            notes="Consulting services",
        )

        inv2 = Invoice(
            org_id=org.id,
            client_id=c1.id,
            number="INV-2025-00002",
            issue_date=date(2025, 11, 2),
            due_date=date(2025, 12, 2),
            currency="ZAR",
            subtotal_cents=10000,
            tax_cents=1500,
            total_cents=11500,
            balance_cents=11500,
            status="draft",
        )

        inv3 = Invoice(
            org_id=org.id,
            client_id=c2.id,
            number="INV-2025-00003",
            issue_date=date(2025, 10, 28),
            due_date=date(2025, 12, 2),
            currency="ZAR",
            subtotal_cents=50000,
            tax_cents=7500,
            total_cents=57500,
            balance_cents=57500,
            status="draft",
        )

        inv4 = Invoice(
            org_id=org.id,
            client_id=c1.id,
            number="INV-2025-00004",
            issue_date=date(2025, 11, 2),
            due_date=date(2025, 12, 2),
            currency="ZAR",
            subtotal_cents=10000,
            tax_cents=1500,
            total_cents=11500,
            balance_cents=11500,
            status="draft",
        )

        inv5 = Invoice(
            org_id=org.id,
            client_id=c1.id,
            number="INV-2025-00005",
            issue_date=date(2025, 11, 2),
            due_date=date(2025, 12, 2),
            currency="ZAR",
            subtotal_cents=10000,
            tax_cents=1500,
            total_cents=11500,
            balance_cents=0,
            status="paid",
        )

        inv6 = Invoice(
            org_id=org.id,
            client_id=c3.id,
            number="INV-2025-00006",
            issue_date=date(2025, 11, 2),
            due_date=date(2025, 12, 2),
            currency="ZAR",
            subtotal_cents=1086957,
            tax_cents=163043,
            total_cents=1250000,
            balance_cents=700000,
            status="partially_paid",
        )

        inv7 = Invoice(
            org_id=org.id,
            client_id=c1.id,
            number="INV-2025-00007",
            issue_date=date(2025, 11, 2),
            due_date=date(2025, 12, 2),
            currency="ZAR",
            subtotal_cents=10000,
            tax_cents=1500,
            total_cents=11500,
            balance_cents=11500,
            status="draft",
        )

        db.add_all([inv1, inv2, inv3, inv4, inv5, inv6, inv7])
        await db.flush()

        # Create invoice items
        items = [
            InvoiceItem(
                invoice_id=inv1.id,
                line_no=1,
                description="Consulting hours",
                qty=10,
                unit_price_cents=10000,
                tax_rate_bp=1500,
                line_total_cents=115000,
            ),
            InvoiceItem(
                invoice_id=inv2.id,
                line_no=1,
                description="Service",
                qty=1,
                unit_price_cents=10000,
                tax_rate_bp=1500,
                line_total_cents=11500,
            ),
            InvoiceItem(
                invoice_id=inv3.id,
                line_no=1,
                description="Service",
                qty=5,
                unit_price_cents=10000,
                tax_rate_bp=1500,
                line_total_cents=57500,
            ),
            InvoiceItem(
                invoice_id=inv4.id,
                line_no=1,
                description="Service",
                qty=1,
                unit_price_cents=10000,
                tax_rate_bp=1500,
                line_total_cents=11500,
            ),
            InvoiceItem(
                invoice_id=inv5.id,
                line_no=1,
                description="Service1",
                qty=1,
                unit_price_cents=10000,
                tax_rate_bp=1500,
                line_total_cents=11500,
            ),
            InvoiceItem(
                invoice_id=inv6.id,
                line_no=1,
                description="Service",
                qty=5,
                unit_price_cents=100000,
                tax_rate_bp=1500,
                line_total_cents=575000,
            ),
            InvoiceItem(
                invoice_id=inv7.id,
                line_no=1,
                description="Service",
                qty=1,
                unit_price_cents=10000,
                tax_rate_bp=1500,
                line_total_cents=11500,
            ),
        ]
        db.add_all(items)

        # Create payments
        payment1 = Payment(
            org_id=org.id,
            invoice_id=inv5.id,
            amount_cents=11500,
            received_at=date(2025, 11, 2),
            method="EFT",
            reference="PAY-001",
            idempotency_key="seed-payment-1",
        )

        payment2 = Payment(
            org_id=org.id,
            invoice_id=inv6.id,
            amount_cents=550000,
            received_at=date(2025, 11, 2),
            method="EFT",
            reference="PAY-002",
            idempotency_key="seed-payment-2",
        )

        db.add_all([payment1, payment2])

        await db.commit()
        print("Seeded complete database:")
        print("  - 1 org, 1 user (admin@example.com / admin123)")
        print("  - 3 clients")
        print("  - 7 invoices (1 draft uppercase, 5 draft lowercase, 1 paid, 1 partially paid)")
        print("  - 7 invoice items")
        print("  - 2 payments")


if __name__ == "__main__":
    asyncio.run(run())
