"""
PostgreSQL-specific payment concurrency tests.

These tests require a real PostgreSQL instance to reproduce SELECT … FOR UPDATE
row-lock semantics.  They are **skipped** automatically when running against the
default SQLite in-memory test database.

To run them, provide a throwaway PostgreSQL database via the environment variable:

    POSTGRES_TEST_DB_URL=postgresql+asyncpg://user:pass@localhost:5432/test_invoicer
    uv run pytest tests/test_payments_pg.py -v

The test database is dropped and recreated for each test module run.
"""

import asyncio
import os
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Invoice, Org, OrgMember, User
from app.security import create_access_token, hash_password

POSTGRES_TEST_DB_URL = os.environ.get("POSTGRES_TEST_DB_URL", "")

requires_postgres = pytest.mark.skipif(
    not POSTGRES_TEST_DB_URL,
    reason=(
        "Set POSTGRES_TEST_DB_URL=postgresql+asyncpg://user:pass@host:5432/test_db "
        "to run PostgreSQL-specific concurrency tests"
    ),
)


# ---------------------------------------------------------------------------
# PostgreSQL-specific fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
async def pg_engine():
    """Create an async engine against the test PostgreSQL database."""
    if not POSTGRES_TEST_DB_URL:
        pytest.skip("No POSTGRES_TEST_DB_URL set")
    engine = create_async_engine(POSTGRES_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def pg_session(pg_engine):
    """Yield an async session and roll back after each test."""
    Session = sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def pg_client(pg_engine):
    """
    HTTPX async client backed by the FastAPI app, patched to use the PostgreSQL
    engine and session maker instead of the default SQLite ones.
    """
    import app.db as db_module
    import app.routers.payments as payments_module
    from app.main import app as fastapi_app

    pg_maker = sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)
    original_engine = db_module.engine
    original_maker = db_module.async_session_maker
    original_use_lock = payments_module._USE_ROW_LOCK

    db_module.engine = pg_engine
    db_module.async_session_maker = pg_maker
    payments_module._USE_ROW_LOCK = True  # enable FOR UPDATE on PostgreSQL

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        yield client

    db_module.engine = original_engine
    db_module.async_session_maker = original_maker
    payments_module._USE_ROW_LOCK = original_use_lock


@pytest.fixture
async def pg_auth_headers(pg_session: AsyncSession):
    """Create org + user in PostgreSQL and return Authorization headers."""
    org = Org(name="PG Test Org")
    pg_session.add(org)
    await pg_session.commit()

    user = User(
        email="pg_test@example.com",
        name="PG Test User",
        password_hash=hash_password("pgpassword123"),
    )
    pg_session.add(user)
    await pg_session.commit()

    membership = OrgMember(org_id=org.id, user_id=user.id, role="OWNER")
    pg_session.add(membership)
    await pg_session.commit()

    token = create_access_token(str(user.id), str(org.id), "OWNER")
    return {"Authorization": f"Bearer {token}", "_org_id": str(org.id)}


@pytest.fixture
async def pg_sent_invoice(pg_session: AsyncSession, pg_auth_headers: dict):
    """Create a sent invoice in PostgreSQL for payment tests."""
    from app.models import Client as ClientModel

    org_id = pg_auth_headers["_org_id"]
    client = ClientModel(org_id=org_id, name="PG Client")
    pg_session.add(client)
    await pg_session.commit()

    inv = Invoice(
        org_id=org_id,
        client_id=client.id,
        number="PG-INV-001",
        issue_date=date.today(),
        due_date=date.today(),
        currency="ZAR",
        subtotal_cents=10000,
        tax_cents=1500,
        total_cents=11500,
        balance_cents=11500,
        status="sent",
        meta={},
    )
    pg_session.add(inv)
    await pg_session.commit()
    await pg_session.refresh(inv)
    return inv


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@requires_postgres
class TestConcurrentPaymentsPostgres:
    """
    Concurrency tests that rely on PostgreSQL SELECT … FOR UPDATE semantics.
    Two simultaneous payment requests against the same invoice must not corrupt
    the invoice balance (no overpayment).
    """

    async def test_concurrent_payments_no_overpayment(
        self,
        pg_client: AsyncClient,
        pg_auth_headers: dict,
        pg_sent_invoice: Invoice,
    ):
        """
        Two concurrent requests each attempting to pay the full invoice amount.
        Exactly one must succeed (balance → 0, status → paid) and the other
        must be rejected with HTTP 400 (amount > remaining balance).
        """
        invoice_id = str(pg_sent_invoice.id)
        headers = {
            "Authorization": pg_auth_headers["Authorization"],
        }
        payment_body = {
            "invoice_id": invoice_id,
            "amount_cents": pg_sent_invoice.total_cents,
            "received_at": str(date.today()),
            "method": "EFT",
        }

        async def pay(key: str):
            return await pg_client.post(
                "/api/v1/payments",
                json=payment_body,
                headers={**headers, "Idempotency-Key": key},
            )

        r1, r2 = await asyncio.gather(pay("concurrent-a"), pay("concurrent-b"))

        statuses = {r1.status_code, r2.status_code}
        # One must succeed (200) and one must be rejected (400)
        assert statuses == {200, 400}, (
            f"Expected one 200 and one 400, got {r1.status_code} and {r2.status_code}"
        )
        success = r1 if r1.status_code == 200 else r2
        assert success.json()["invoice_status"] == "paid"
        assert success.json()["balance_cents"] == 0

    async def test_concurrent_same_idempotency_key_no_duplicate_payment(
        self,
        pg_client: AsyncClient,
        pg_auth_headers: dict,
        pg_sent_invoice: Invoice,
    ):
        """
        Two concurrent requests with the same idempotency key must produce exactly
        one payment record.  The second call returns the same payment_id (idempotent).
        """
        invoice_id = str(pg_sent_invoice.id)
        headers = {"Authorization": pg_auth_headers["Authorization"]}
        body = {
            "invoice_id": invoice_id,
            "amount_cents": 100,
            "received_at": str(date.today()),
        }

        async def pay():
            return await pg_client.post(
                "/api/v1/payments",
                json=body,
                headers={**headers, "Idempotency-Key": "pg-idem-race-001"},
            )

        r1, r2 = await asyncio.gather(pay(), pay())

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["payment_id"] == r2.json()["payment_id"]
