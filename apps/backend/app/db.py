import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def create_engine_with_config() -> AsyncEngine:
    # SQLite needs different connect args than PostgreSQL; centralises that branching so the rest of the app works across different variations.
    # Step 1: Detect SQLite vs PostgreSQL URL;
    # Step 2: Create async engine with matching pool/echo config.
    if settings.database_url.startswith("sqlite"):
        return create_async_engine(
            settings.database_url,
            echo=settings.is_development,
            connect_args={"check_same_thread": False},
        )
    else:
        return create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_recycle=settings.db_pool_recycle,
            pool_pre_ping=settings.db_pool_pre_ping,
            echo=settings.is_development,
        )


@retry(
    stop=stop_after_attempt(settings.db_startup_retry_attempts),
    wait=wait_exponential(multiplier=1, min=2, max=settings.db_startup_retry_max_wait),
    retry=retry_if_exception_type(OperationalError),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def verify_db_connection(engine: AsyncEngine) -> None:
    # Fails fast at startup with retries so a bad DB URL surfaces immediately rather than on the first real request.
    # Step 1: Open connection;
    # Step 2: Execute SELECT 1;
    # Step 3: Retry up to N times on OperationalError.
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection verified")


engine: AsyncEngine = create_engine_with_config()

async_session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # Yields a per-request session from the pool so each request gets its own isolated transaction context.
    # Step 1: Open a session from the connection pool;
    # Step 2: Yield to caller; Step 3: Auto-close on exit.
    async with async_session_maker() as session:
        yield session
