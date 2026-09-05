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

        assert response.status_code == 201
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

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Client"
        assert data["email"] is None
        assert data["billing_address"] is None


@pytest.mark.unit
class TestClientCRUD:
    """Tests for GET, PATCH, DELETE /clients/{id}."""

    async def test_get_client_success(self, authenticated_client: AsyncClient, test_client_record):
        resp = await authenticated_client.get(f"/api/v1/clients/{test_client_record.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(test_client_record.id)
        assert resp.json()["name"] == test_client_record.name

    async def test_get_client_not_found(self, authenticated_client: AsyncClient):
        resp = await authenticated_client.get(
            "/api/v1/clients/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == 404

    async def test_get_client_cross_tenant(
        self, authenticated_client: AsyncClient, other_org_client_record
    ):
        """Cross-tenant lookup returns 404, not 403, to avoid resource enumeration."""
        resp = await authenticated_client.get(f"/api/v1/clients/{other_org_client_record.id}")
        assert resp.status_code == 404

    async def test_update_client_success(
        self, authenticated_client: AsyncClient, test_client_record
    ):
        resp = await authenticated_client.patch(
            f"/api/v1/clients/{test_client_record.id}",
            json={"name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        # Unchanged fields stay
        assert resp.json()["email"] == test_client_record.email

    async def test_update_client_member_forbidden(
        self, member_authenticated_client, test_client_record
    ):
        resp = await member_authenticated_client.patch(
            f"/api/v1/clients/{test_client_record.id}",
            json={"name": "Hacked"},
        )
        assert resp.status_code == 403

    async def test_update_client_not_found(self, authenticated_client: AsyncClient):
        resp = await authenticated_client.patch(
            "/api/v1/clients/00000000-0000-0000-0000-000000000000",
            json={"name": "Updated"},
        )
        assert resp.status_code == 404

    async def test_update_client_cross_tenant(
        self, authenticated_client: AsyncClient, other_org_client_record
    ):
        resp = await authenticated_client.patch(
            f"/api/v1/clients/{other_org_client_record.id}",
            json={"name": "Updated"},
        )
        assert resp.status_code == 404

    async def test_delete_client_success(
        self, authenticated_client: AsyncClient, test_client_record
    ):
        resp = await authenticated_client.delete(f"/api/v1/clients/{test_client_record.id}")
        assert resp.status_code == 204
        # Verify gone
        get_resp = await authenticated_client.get(f"/api/v1/clients/{test_client_record.id}")
        assert get_resp.status_code == 404

    async def test_delete_client_member_forbidden(
        self, member_authenticated_client, test_client_record
    ):
        resp = await member_authenticated_client.delete(f"/api/v1/clients/{test_client_record.id}")
        assert resp.status_code == 403

    async def test_delete_client_with_invoices_conflict(
        self, authenticated_client: AsyncClient, client_with_invoice
    ):
        """Deleting a client referenced by an invoice returns 409."""
        resp = await authenticated_client.delete(f"/api/v1/clients/{client_with_invoice.id}")
        assert resp.status_code == 409

    async def test_delete_client_is_soft_delete(
        self, authenticated_client: AsyncClient, test_client_record
    ):
        """Deletion sets deleted_at rather than removing the row, and the client
        disappears from both list and search results."""
        resp = await authenticated_client.delete(f"/api/v1/clients/{test_client_record.id}")
        assert resp.status_code == 204

        list_resp = await authenticated_client.get("/api/v1/clients")
        assert list_resp.status_code == 200
        assert all(c["id"] != str(test_client_record.id) for c in list_resp.json())

        search_resp = await authenticated_client.get(
            f"/api/v1/clients?q={test_client_record.name.split()[0]}"
        )
        assert all(c["id"] != str(test_client_record.id) for c in search_resp.json())


@pytest.mark.unit
class TestClientSearch:
    """Tests for the q= search parameter on GET /clients."""

    async def test_search_by_name(self, authenticated_client: AsyncClient, test_client_record):
        resp = await authenticated_client.get("/api/v1/clients?q=Test+Client")
        assert resp.status_code == 200
        data = resp.json()
        assert any(c["id"] == str(test_client_record.id) for c in data)

    async def test_search_by_email(self, authenticated_client: AsyncClient, test_client_record):
        resp = await authenticated_client.get("/api/v1/clients?q=example.com")
        assert resp.status_code == 200
        data = resp.json()
        assert any(c["id"] == str(test_client_record.id) for c in data)

    async def test_search_case_insensitive(
        self, authenticated_client: AsyncClient, test_client_record
    ):
        resp = await authenticated_client.get("/api/v1/clients?q=test+client")
        assert resp.status_code == 200
        data = resp.json()
        assert any(c["id"] == str(test_client_record.id) for c in data)

    async def test_search_no_matches(self, authenticated_client: AsyncClient, test_client_record):  # noqa: ARG002
        resp = await authenticated_client.get("/api/v1/clients?q=xyzz_not_exist_abc")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_search_tenant_isolation(
        self, authenticated_client: AsyncClient, other_org_client_record
    ):
        """Search never returns clients from another organisation."""
        resp = await authenticated_client.get("/api/v1/clients?q=Other+Org")
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.json()]
        assert str(other_org_client_record.id) not in ids

    async def test_search_empty_returns_all_own(
        self, authenticated_client: AsyncClient, test_client_record
    ):
        resp = await authenticated_client.get("/api/v1/clients")
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.json()]
        assert str(test_client_record.id) in ids


@pytest.mark.unit
class TestCreateClientRBAC:
    """RBAC: MEMBER cannot mutate clients."""

    async def test_create_client_member_forbidden(self, member_authenticated_client):
        resp = await member_authenticated_client.post(
            "/api/v1/clients", json={"name": "Should Fail"}
        )
        assert resp.status_code == 403
