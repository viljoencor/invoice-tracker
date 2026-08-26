"""Tests for invoice management endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestInvoices:
    """Test invoice management endpoints."""

    async def test_create_invoice(self, authenticated_client: AsyncClient, mock_invoice_data):
        """Test creating a new invoice."""
        response = await authenticated_client.post(
            "/api/v1/invoices",
            json=mock_invoice_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "number" in data
        assert data["status"] == "draft"
        assert data["total_cents"] == 11500  # 10000 + 15% tax

    async def test_create_invoice_invalid_client(
        self, authenticated_client: AsyncClient, mock_invoice_data
    ):
        """Test creating invoice with invalid client fails."""
        mock_invoice_data["client_id"] = "00000000-0000-0000-0000-000000000000"
        response = await authenticated_client.post(
            "/api/v1/invoices",
            json=mock_invoice_data,
        )

        assert response.status_code == 404

    async def test_list_invoices(self, authenticated_client: AsyncClient):
        """Test listing invoices."""
        response = await authenticated_client.get("/api/v1/invoices")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_invoice_detail(self, authenticated_client: AsyncClient, mock_invoice_data):
        """Test retrieving invoice details."""
        # First create an invoice
        create_response = await authenticated_client.post(
            "/api/v1/invoices",
            json=mock_invoice_data,
        )
        invoice_id = create_response.json()["id"]

        # Now get its details
        response = await authenticated_client.get(f"/api/v1/invoices/{invoice_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == invoice_id
        assert "client_name" in data

    async def test_get_invoice_pdf(self, authenticated_client: AsyncClient, mock_invoice_data):
        """Test generating invoice PDF."""
        # First create an invoice
        create_response = await authenticated_client.post(
            "/api/v1/invoices",
            json=mock_invoice_data,
        )
        invoice_id = create_response.json()["id"]

        # Request PDF
        response = await authenticated_client.get(f"/api/v1/invoices/{invoice_id}/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0

    @pytest.mark.skip(
        reason="date_trunc is PostgreSQL-specific, not supported in SQLite test environment"
    )
    async def test_invoice_summary(self, authenticated_client: AsyncClient):
        """Test getting invoice summary statistics."""
        response = await authenticated_client.get("/api/v1/invoices/summary")

        assert response.status_code == 200
        data = response.json()
        assert "total_due_cents" in data
        assert "overdue_count" in data
        assert "revenue_by_month" in data
        assert isinstance(data["revenue_by_month"], list)

    async def test_mark_invoice_sent(self, authenticated_client: AsyncClient, mock_invoice_data):
        """Test marking invoice as sent."""
        # Create invoice
        create_response = await authenticated_client.post(
            "/api/v1/invoices",
            json=mock_invoice_data,
        )
        invoice_id = create_response.json()["id"]

        # Mark as sent
        response = await authenticated_client.post(f"/api/v1/invoices/{invoice_id}/send")

        assert response.status_code == 200
        data = response.json()
        assert data["invoice_status"] == "sent"
