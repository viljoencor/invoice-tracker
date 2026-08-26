"""Tests for authentication endpoints. Tests"""

import pytest
from httpx import AsyncClient

from app.security import create_access_token


@pytest.mark.unit
class TestAuth:
    """Test authentication endpoints."""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration returns access and refresh tokens."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "New User",
                "email": "newuser@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["refresh_token"]) > 0

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with duplicate email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Another User",
                "email": test_user.email,
                "password": "password123",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login returns access and refresh tokens."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncClient, test_user):
        """Test login with invalid credentials fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 401


@pytest.mark.unit
class TestGetMe:
    """Tests for GET /auth/me."""

    async def test_me_success(self, authenticated_client: AsyncClient, test_user, test_org):
        response = await authenticated_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["id"] == str(test_user.id)
        assert data["org_id"] == str(test_org.id)
        assert data["role"] == "OWNER"

    async def test_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403

    async def test_me_invalid_user(self, client):
        """JWT with non-existent user returns 404."""
        fake_token = create_access_token(
            "00000000-0000-0000-0000-000000000000",
            "00000000-0000-0000-0000-000000000001",
            "OWNER",
        )
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {fake_token}"}
        )
        assert resp.status_code == 404


@pytest.mark.unit
class TestRefreshTokens:
    """Tests for refresh-token rotation and logout."""

    async def test_refresh_success(self, client: AsyncClient, test_user):
        """A valid refresh token yields new access and refresh tokens."""
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        tokens = login.json()

        resp = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert resp.status_code == 200
        new_tokens = resp.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["refresh_token"] != tokens["refresh_token"]

    async def test_refresh_rotation_replay_rejected(self, client: AsyncClient, test_user):
        """After rotation, replaying the old token must be rejected."""
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        old_refresh = login.json()["refresh_token"]

        resp1 = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert resp1.status_code == 200

        # Replay the original token — must fail
        resp2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert resp2.status_code == 401

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """A made-up token is rejected."""
        resp = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "totally-not-a-real-token"}
        )
        assert resp.status_code == 401

    async def test_logout_success(self, client: AsyncClient, test_user):
        """Logout returns 204."""
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        refresh = login.json()["refresh_token"]

        resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
        assert resp.status_code == 204

    async def test_logout_revokes_token(self, client: AsyncClient, test_user):
        """Token cannot be used for refresh after logout."""
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        refresh = login.json()["refresh_token"]

        await client.post("/api/v1/auth/logout", json={"refresh_token": refresh})

        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 401

    async def test_logout_unknown_token_is_silent(self, client):
        """Logout with an unknown token still returns 204 (no information leak)."""
        resp = await client.post("/api/v1/auth/logout", json={"refresh_token": "unknown-token-xyz"})
        assert resp.status_code == 204
