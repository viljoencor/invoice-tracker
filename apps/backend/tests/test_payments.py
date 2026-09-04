"""Tests for payment endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestPayments:
    """Test payment management endpoints."""

    async def test_apply_payment(self, authenticated_client: AsyncClient, mock_invoice_data):
        """Test applying a payment to an invoice."""
        from datetime import date

        # First create an invoice and mark it as sent
        create_response = await authenticated_client.post(
            "/api/v1/invoices",
            json=mock_invoice_data,
            headers={"Idempotency-Key": "test-invoice-apply-payment"},
        )
        invoice_id = create_response.json()["id"]

        await authenticated_client.post(f"/api/v1/invoices/{invoice_id}/send")

        # Apply payment
        response = await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": 5000,
                "received_at": str(date.today()),
                "method": "EFT",
                "reference": "TEST-REF-001",
            },
            headers={"Idempotency-Key": "test-payment-001"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "payment_id" in data
        assert data["invoice_status"] == "partially_paid"
        assert data["balance_cents"] == 6500  # 11500 - 5000

    async def test_apply_payment_full_amount(
        self, authenticated_client: AsyncClient, mock_invoice_data
    ):
        """Test applying full payment to an invoice."""
        from datetime import date

        # Create and send invoice
        create_response = await authenticated_client.post(
            "/api/v1/invoices",
            json=mock_invoice_data,
            headers={"Idempotency-Key": "test-invoice-full-amount"},
        )
        invoice_id = create_response.json()["id"]
        total_cents = create_response.json()["total_cents"]

        await authenticated_client.post(f"/api/v1/invoices/{invoice_id}/send")

        # Pay full amount
        response = await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": total_cents,
                "received_at": str(date.today()),
                "method": "EFT",
            },
            headers={"Idempotency-Key": "test-payment-full"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["invoice_status"] == "paid"
        assert data["balance_cents"] == 0

    async def test_payment_idempotency(self, authenticated_client: AsyncClient, mock_invoice_data):
        """Test payment idempotency key prevents duplicate payments."""
        from datetime import date

        # Create and send invoice
        create_response = await authenticated_client.post(
            "/api/v1/invoices",
            json=mock_invoice_data,
            headers={"Idempotency-Key": "test-invoice-payment-idem"},
        )
        invoice_id = create_response.json()["id"]

        await authenticated_client.post(f"/api/v1/invoices/{invoice_id}/send")

        payment_data = {
            "invoice_id": invoice_id,
            "amount_cents": 5000,
            "received_at": str(date.today()),
            "method": "EFT",
        }

        # Apply payment first time
        response1 = await authenticated_client.post(
            "/api/v1/payments",
            json=payment_data,
            headers={"Idempotency-Key": "test-idem-001"},
        )

        assert response1.status_code == 200
        payment_id = response1.json()["payment_id"]

        # Apply same payment again with same idempotency key
        response2 = await authenticated_client.post(
            "/api/v1/payments",
            json=payment_data,
            headers={"Idempotency-Key": "test-idem-001"},
        )

        assert response2.status_code == 200
        assert response2.json()["payment_id"] == payment_id
        assert "idempotent-return" in response2.json().get("note", "")

    async def test_apply_payment_missing_idempotency_key(
        self, authenticated_client: AsyncClient, mock_invoice_data
    ):
        """Test payment without idempotency key fails."""
        from datetime import date

        create_response = await authenticated_client.post(
            "/api/v1/invoices",
            json=mock_invoice_data,
            headers={"Idempotency-Key": "test-invoice-missing-payment-key"},
        )
        invoice_id = create_response.json()["id"]

        response = await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": 5000,
                "received_at": str(date.today()),
            },
        )

        assert response.status_code == 400
        assert "idempotency" in response.json()["detail"].lower()

    async def test_list_payments(self, authenticated_client: AsyncClient, mock_invoice_data):
        """Test listing payments for an invoice."""
        from datetime import date

        # Create invoice and apply payment
        create_response = await authenticated_client.post(
            "/api/v1/invoices",
            json=mock_invoice_data,
            headers={"Idempotency-Key": "test-invoice-list-payments"},
        )
        invoice_id = create_response.json()["id"]

        await authenticated_client.post(f"/api/v1/invoices/{invoice_id}/send")

        await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": 5000,
                "received_at": str(date.today()),
                "method": "EFT",
            },
            headers={"Idempotency-Key": "test-list-001"},
        )

        # List payments
        response = await authenticated_client.get(f"/api/v1/payments?invoice_id={invoice_id}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["amount_cents"] == 5000
