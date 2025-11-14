import os

os.environ.setdefault("JWT_SECRET", "test-secret-key-that-is-at-least-32-characters-long")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import Base
from app.models import Client, Org, OrgMember, User
from app.security import hash_password

from app.db import engine
from app.db import async_session_maker
from app.security import create_access_token
from app.main import app as fastapi_app
from httpx import ASGITransport
from datetime import date, timedelta

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:

    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def test_org(db_session: AsyncSession) -> Org:
    org = Org(name="Test Organization")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_user(db_session: AsyncSession, test_org: Org) -> User:
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash=hash_password("testpassword123"),
    )
    db_session.add(user)
    await db_session.commit()

    membership = OrgMember(org_id=test_org.id, user_id=user.id, role="OWNER")
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_client_record(db_session: AsyncSession, test_org: Org) -> Client:
    client = Client(
        org_id=test_org.id,
        name="Test Client Ltd",
        email="client@example.com",
        billing_address="123 Test Street, Test City",
    )
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    return client


@pytest.fixture
async def auth_token(test_user: User, test_org: Org) -> str:

    return create_access_token(str(test_user.id), str(test_org.id))


@pytest.fixture
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client: AsyncClient, auth_token: str) -> AsyncClient:
    client.headers["Authorization"] = f"Bearer {auth_token}"
    return client


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        environment="development",
        database_url=TEST_DATABASE_URL,
        jwt_secret="_Bk2swV-irvgVGswT169WWh4ty2DFVgvTS9q3_KtlHo",
        rate_limit_enabled=False,
    )


@pytest.fixture
def mock_invoice_data(test_client_record: Client) -> dict:

    return {
        "client_id": str(test_client_record.id),
        "issue_date": str(date.today()),
        "due_date": str(date.today() + timedelta(days=30)),
        "currency": "ZAR",
        "notes": "Test invoice",
        "items": [
            {
                "description": "Test Service",
                "qty": 1.0,
                "unit_price_cents": 10000,
                "tax_rate_bp": 1500,
            }
        ],
    }
