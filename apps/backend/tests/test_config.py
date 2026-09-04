"""Tests for Settings validators (production guards on secrets/credentials)."""

import pytest
from pydantic import ValidationError

from app.config import Settings


class TestJwtSecretValidator:
    def test_rejects_default_secret_in_production(self):
        with pytest.raises(ValidationError):
            Settings(environment="production", jwt_secret="change-me")

    def test_allows_strong_secret_in_production(self):
        s = Settings(environment="production", jwt_secret="x" * 32)
        assert s.jwt_secret == "x" * 32

    def test_rejects_short_secret_regardless_of_environment(self):
        with pytest.raises(ValidationError):
            Settings(environment="development", jwt_secret="too-short")


class TestDatabaseUrlValidator:
    def test_rejects_default_database_url_in_production(self):
        with pytest.raises(ValidationError):
            Settings(
                environment="production",
                jwt_secret="x" * 32,
                database_url="postgresql+asyncpg://postgres:postgres@db:5432/invoicer",
            )

    def test_allows_default_database_url_in_development(self):
        s = Settings(
            environment="development",
            jwt_secret="x" * 32,
            database_url="postgresql+asyncpg://postgres:postgres@db:5432/invoicer",
        )
        assert s.environment == "development"

    def test_allows_custom_database_url_in_production(self):
        s = Settings(
            environment="production",
            jwt_secret="x" * 32,
            database_url="postgresql+asyncpg://real_user:real_pass@prod-db:5432/invoicer",
        )
        assert "real_user" in s.database_url
