"""RBAC permission matrix tests for invoices and payments.

Permission matrix (✓=allowed, ✗=denied):
  Endpoint                       OWNER   MEMBER  No Auth
  POST   /invoices                ✓       ✗       ✗
  GET    /invoices                ✓       ✓       ✗
  GET    /invoices/{id}           ✓       ✓       ✗
  POST   /invoices/{id}/send      ✓       ✗       ✗
  POST   /payments                ✓       ✗       ✗
  GET    /payments                ✓       ✓       ✗
"""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestInvoiceRBAC:
    """RBAC enforcement on invoice mutation endpoints."""

    async def test_create_invoice_member_forbidden(
        self, member_authenticated_client, mock_invoice_data
    ):
        resp = await member_authenticated_client.post("/api/v1/invoices", json=mock_invoice_data)
        assert resp.status_code == 403

    async def test_create_invoice_unauthenticated(self, client: AsyncClient, mock_invoice_data):
        resp = await client.post("/api/v1/invoices", json=mock_invoice_data)
        assert resp.status_code == 403

    async def test_list_invoices_member_allowed(self, member_authenticated_client):
        """MEMBER can read invoices."""
        resp = await member_authenticated_client.get("/api/v1/invoices")
        assert resp.status_code == 200

    async def test_mark_sent_member_forbidden(
        self, authenticated_client: AsyncClient, member_authenticated_client, mock_invoice_data
    ):
        """OWNER creates invoice, MEMBER cannot mark it sent."""
        create_resp = await authenticated_client.post("/api/v1/invoices", json=mock_invoice_data)
        assert create_resp.status_code == 201
        invoice_id = create_resp.json()["id"]

        resp = await member_authenticated_client.post(f"/api/v1/invoices/{invoice_id}/send")
        assert resp.status_code == 403

    async def test_mark_sent_owner_allowed(
        self, authenticated_client: AsyncClient, mock_invoice_data
    ):
        """OWNER can mark an invoice as sent."""
        create_resp = await authenticated_client.post("/api/v1/invoices", json=mock_invoice_data)
        invoice_id = create_resp.json()["id"]

        resp = await authenticated_client.post(f"/api/v1/invoices/{invoice_id}/send")
        assert resp.status_code == 200


@pytest.mark.unit
class TestPaymentRBAC:
    """RBAC enforcement on payment mutation endpoints."""

    async def test_apply_payment_member_forbidden(
        self,
        authenticated_client: AsyncClient,
        member_authenticated_client,
        mock_invoice_data,
    ):
        """MEMBER cannot apply payments."""
        from datetime import date

        create_resp = await authenticated_client.post("/api/v1/invoices", json=mock_invoice_data)
        invoice_id = create_resp.json()["id"]
        await authenticated_client.post(f"/api/v1/invoices/{invoice_id}/send")

        resp = await member_authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": 5000,
                "received_at": str(date.today()),
                "method": "EFT",
            },
            headers={"Idempotency-Key": "rbac-test-001"},
        )
        assert resp.status_code == 403

    async def test_list_payments_member_allowed(
        self,
        authenticated_client: AsyncClient,
        member_authenticated_client,
        mock_invoice_data,
    ):
        """MEMBER can read payments."""
        create_resp = await authenticated_client.post("/api/v1/invoices", json=mock_invoice_data)
        invoice_id = create_resp.json()["id"]

        resp = await member_authenticated_client.get(f"/api/v1/payments?invoice_id={invoice_id}")
        assert resp.status_code == 200
