import logging

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
    """Create database engine with production-ready configuration."""
    # SQLite doesn't support pool_size/max_overflow, only use them for PostgreSQL
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
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(OperationalError),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def verify_db_connection(engine: AsyncEngine) -> None:
    """Verify database connection with retry logic."""
    from sqlalchemy import text

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection verified successfully")


# Create engine with configuration
engine: AsyncEngine = create_engine_with_config()

async_session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
