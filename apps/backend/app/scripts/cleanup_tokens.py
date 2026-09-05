"""Deletes revoked or expired refresh tokens.

Run periodically (cron / scheduled task) to keep the refresh_tokens table
from growing unboundedly, since login/refresh/logout only ever mark rows
revoked rather than deleting them:

    python -m app.scripts.cleanup_tokens
"""

import asyncio
from datetime import UTC, datetime

from sqlalchemy import delete, or_

from app.db import async_session_maker
from app.logging_config import get_logger
from app.models import RefreshToken

logger = get_logger(__name__)


async def run() -> int:
    now = datetime.now(UTC)
    async with async_session_maker() as db:
        result = await db.execute(
            delete(RefreshToken).where(
                or_(RefreshToken.revoked.is_(True), RefreshToken.expires_at < now)
            )
        )
        await db.commit()
        deleted = result.rowcount or 0
        logger.info("refresh_tokens.cleanup", deleted=deleted)
        return deleted


if __name__ == "__main__":
    count = asyncio.run(run())
    print(f"Deleted {count} revoked/expired refresh token(s).")
