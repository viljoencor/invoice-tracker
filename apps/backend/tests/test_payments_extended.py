"""Extended payment tests — overpayment, sequential balance integrity, status transitions."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _create_and_send_invoice(client: AsyncClient, mock_invoice_data: dict) -> tuple:
    """Create an invoice via the API, mark it sent, return (invoice_id, total_cents)."""
    idem_key = f"test-extended-{uuid.uuid4()}"
    resp = await client.post(
        "/api/v1/invoices", json=mock_invoice_data, headers={"Idempotency-Key": idem_key}
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    invoice_id = data["id"]
    total_cents = data["total_cents"]
    send_resp = await client.post(f"/api/v1/invoices/{invoice_id}/send")
    assert send_resp.status_code == 200
    return invoice_id, total_cents


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestPaymentLogicExtended:
    async def test_overpayment_rejected(
        self, authenticated_client: AsyncClient, mock_invoice_data: dict
    ):
        """Payment amount > invoice balance must be rejected with 400."""
        invoice_id, total_cents = await _create_and_send_invoice(
            authenticated_client, mock_invoice_data
        )

        resp = await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": total_cents + 1,
                "received_at": str(date.today()),
                "method": "EFT",
            },
            headers={"Idempotency-Key": "overpay-001"},
        )

        assert resp.status_code == 400
        assert "invalid" in resp.json()["detail"].lower()

    async def test_zero_amount_rejected(
        self, authenticated_client: AsyncClient, mock_invoice_data: dict
    ):
        """Zero-amount payment is rejected (Pydantic schema enforces amount_cents > 0)."""
        invoice_id, _ = await _create_and_send_invoice(authenticated_client, mock_invoice_data)

        resp = await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": 0,
                "received_at": str(date.today()),
            },
            headers={"Idempotency-Key": "zero-001"},
        )

        # 422 from Pydantic (amount_cents must be > 0) or 400 from handler
        assert resp.status_code in (400, 422)

    async def test_partial_then_full_payment_sequence(
        self, authenticated_client: AsyncClient, mock_invoice_data: dict
    ):
        """Two payments summing to the invoice total result in paid status with balance 0."""
        invoice_id, total_cents = await _create_and_send_invoice(
            authenticated_client, mock_invoice_data
        )
        partial = total_cents // 2

        # First: partial
        r1 = await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": partial,
                "received_at": str(date.today()),
                "method": "EFT",
            },
            headers={"Idempotency-Key": "seq-001"},
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["invoice_status"] == "partially_paid"
        assert d1["balance_cents"] == total_cents - partial

        # Second: remainder (exactly)
        remainder = total_cents - partial
        r2 = await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": remainder,
                "received_at": str(date.today()),
                "method": "EFT",
            },
            headers={"Idempotency-Key": "seq-002"},
        )
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["invoice_status"] == "paid"
        assert d2["balance_cents"] == 0

    async def test_cannot_overpay_after_partial_payment(
        self, authenticated_client: AsyncClient, mock_invoice_data: dict
    ):
        """Paying more than the remaining balance after a partial payment is rejected."""
        invoice_id, total_cents = await _create_and_send_invoice(
            authenticated_client, mock_invoice_data
        )
        partial = total_cents // 2

        # Partial payment
        r1 = await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": partial,
                "received_at": str(date.today()),
            },
            headers={"Idempotency-Key": "partial-over-001"},
        )
        assert r1.status_code == 200

        # Try to pay the full original total (more than remaining balance)
        r2 = await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": total_cents,  # > remaining balance
                "received_at": str(date.today()),
            },
            headers={"Idempotency-Key": "partial-over-002"},
        )
        assert r2.status_code == 400
        assert "invalid" in r2.json()["detail"].lower()

    async def test_payment_on_paid_invoice_rejected(
        self, authenticated_client: AsyncClient, mock_invoice_data: dict
    ):
        """Applying a payment to an already-paid invoice must return 400."""
        invoice_id, total_cents = await _create_and_send_invoice(
            authenticated_client, mock_invoice_data
        )

        # Pay in full
        r1 = await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": total_cents,
                "received_at": str(date.today()),
            },
            headers={"Idempotency-Key": "paid-guard-001"},
        )
        assert r1.status_code == 200
        assert r1.json()["invoice_status"] == "paid"

        # Attempt second payment → balance is 0, status is "paid"
        r2 = await authenticated_client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount_cents": 1,
                "received_at": str(date.today()),
            },
            headers={"Idempotency-Key": "paid-guard-002"},
        )
        assert r2.status_code == 400
        assert "paid" in r2.json()["detail"].lower()

    async def test_idempotency_race_simulation(
        self, authenticated_client: AsyncClient, mock_invoice_data: dict
    ):
        """
        Sequential simulation of a concurrent race on the same idempotency key.

        The double-check-inside-lock logic ensures that, regardless of the order
        in which the two calls read/write, exactly one payment is created.
        PostgreSQL-level concurrency is verified in test_payments_pg.py.
        """
        invoice_id, _ = await _create_and_send_invoice(authenticated_client, mock_invoice_data)

        common_key = "race-idem-001"
        payment_body = {
            "invoice_id": invoice_id,
            "amount_cents": 100,
            "received_at": str(date.today()),
        }

        r1 = await authenticated_client.post(
            "/api/v1/payments",
            json=payment_body,
            headers={"Idempotency-Key": common_key},
        )
        r2 = await authenticated_client.post(
            "/api/v1/payments",
            json=payment_body,
            headers={"Idempotency-Key": common_key},
        )

        assert r1.status_code == 200
        assert r2.status_code == 200
        # Both return success but only one payment was created
        assert r1.json()["payment_id"] == r2.json()["payment_id"]
        assert r2.json().get("note") == "idempotent-return"
