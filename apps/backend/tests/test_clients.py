"""Tests for client management endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestClients:
    """Test client management endpoints."""

    async def test_create_client(self, authenticated_client: AsyncClient):
        """Test creating a new client."""
        response = await authenticated_client.post(
            "/api/v1/clients",
            json={
                "name": "New Client Corp",
                "email": "contact@newclient.com",
                "billing_address": "456 Business Ave, Commerce City",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Client Corp"
        assert data["email"] == "contact@newclient.com"
        assert "id" in data

    async def test_create_client_unauthenticated(self, client: AsyncClient):
        """Test creating client without authentication fails."""
        response = await client.post(
            "/api/v1/clients",
            json={
                "name": "Test Client",
                "email": "test@client.com",
            },
        )

        assert response.status_code == 403

    async def test_list_clients(self, authenticated_client: AsyncClient, test_client_record):
        """Test listing clients."""
        response = await authenticated_client.get("/api/v1/clients")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Check if our test client is in the list
        client_names = [c["name"] for c in data]
        assert test_client_record.name in client_names

    async def test_list_clients_unauthenticated(self, client: AsyncClient):
        """Test listing clients without authentication fails."""
        response = await client.get("/api/v1/clients")
        assert response.status_code == 403

    async def test_create_client_minimal_data(self, authenticated_client: AsyncClient):
        """Test creating client with only required fields."""
        response = await authenticated_client.post(
            "/api/v1/clients",
            json={"name": "Minimal Client"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Client"
        assert data["email"] is None
        assert data["billing_address"] is None
