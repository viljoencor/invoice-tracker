import logging
import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.engine import create_engine
from sqlalchemy.exc import ProgrammingError

# Add root logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = context.config

# Read the database URL from the environment; strip the async driver suffix
# because Alembic uses synchronous SQLAlchemy (psycopg2 / psycopg).
_raw_url = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@db:5432/invoicer"
)
database_url = _raw_url.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models
from app import models  # noqa
target_metadata = models.Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    logger.info(f"Running offline migrations with URL: {url}")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    # Use create_engine directly for better control
    url = config.get_main_option("sqlalchemy.url")
    logger.info(f"Running online migrations with URL: {url}")
    
    engine = create_engine(url)
    
    with engine.connect() as connection:
        # Try to create pg_trgm extension
        try:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            connection.commit()
            logger.info("Successfully created pg_trgm extension")
        except ProgrammingError as e:
            logger.warning(f"Could not create pg_trgm extension: {e}")
            connection.rollback()
        except Exception as e:
            logger.error(f"Unexpected error creating pg_trgm extension: {e}")
            connection.rollback()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )
        
        try:
            with context.begin_transaction():
                logger.info("Starting migration transaction")
                context.run_migrations()
                logger.info("Completed migrations successfully")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
