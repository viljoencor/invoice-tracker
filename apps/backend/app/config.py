import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    environment: str = Field(
        default="development", description="Environment: development, staging, production"
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/invoicer"
    db_pool_size: int = Field(default=20, ge=1, le=100)
    db_max_overflow: int = Field(default=10, ge=0, le=50)
    db_pool_recycle: int = Field(default=3600, ge=300)  # seconds
    db_pool_pre_ping: bool = True

    # Database startup retry
    db_startup_retry_attempts: int = Field(default=5, ge=1, le=20)
    db_startup_retry_max_wait: int = Field(default=10, ge=1, le=60)

    # Security
    jwt_secret: str = Field(default="change-me")
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 12

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # Logging
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_json_format: bool = True

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        env = info.data.get("environment", os.getenv("ENVIRONMENT", "development"))

        if env == "production" and v == "change-me":
            raise ValueError(
                "JWT_SECRET must be changed in production. "
                "Set a strong, random secret (min 32 characters) via environment variable."
            )

        if len(v) < 32:
            raise ValueError(
                f"JWT_SECRET must be at least 32 characters long. Current length: {len(v)}"
            )

        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of: {', '.join(allowed)}")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


settings = Settings()
