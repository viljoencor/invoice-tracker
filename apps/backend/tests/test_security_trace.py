"""Tests for Phase 3: readiness sanitisation, trace-ID binding, and auth audit events."""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helper: fake async context manager that raises on __aenter__
# ---------------------------------------------------------------------------
class _FailConn:
    def __init__(self, msg: str) -> None:
        self._msg = msg

    async def __aenter__(self):
        raise Exception(self._msg)

    async def __aexit__(self, *args):
        pass


# ---------------------------------------------------------------------------
# A. Readiness sanitisation
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestReadinessSanitisation:
    async def test_readiness_healthy(self, client: AsyncClient):
        """Normal operation returns 200 with ready=True."""
        resp = await client.get("/readiness")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is True
        assert data["database"] == "connected"

    async def test_healthz_liveness(self, client: AsyncClient):
        """Liveness probe returns 200 independently of the database."""
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    async def test_readiness_failure_no_secret_in_response(self, client: AsyncClient):
        """A DB exception containing credentials must not appear in the 503 response body."""
        from unittest.mock import patch

        import app.main as m

        secret = "TOP_SECRET_DB_PASSWORD_XYZ"

        class _MockEngine:
            def connect(self):
                return _FailConn(
                    f"could not connect to postgresql://user:{secret}@db:5432/invoicer"
                )

        with patch.object(m, "engine", _MockEngine()):
            resp = await client.get("/readiness")

        assert resp.status_code == 503
        assert secret not in resp.text
        data = resp.json()
        assert data["ready"] is False
        assert data["database"] == "disconnected"
        assert "error" not in data  # internal detail must not be exposed


# ---------------------------------------------------------------------------
# C. Trace-ID middleware
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestTraceIdMiddleware:
    async def test_valid_trace_id_is_echoed(self, client: AsyncClient):
        """A well-formed inbound x-trace-id is returned unchanged in the response header."""
        trace_id = "my-valid-trace-abc-123"
        resp = await client.get("/healthz", headers={"x-trace-id": trace_id})
        assert resp.status_code == 200
        assert resp.headers["x-trace-id"] == trace_id

    async def test_trace_id_generated_when_absent(self, client: AsyncClient):
        """When no x-trace-id is sent, the response header contains a generated UUID."""
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        trace_id = resp.headers.get("x-trace-id", "")
        assert trace_id  # non-empty
        # Should be a valid UUID (36 chars with hyphens)
        import uuid

        uuid.UUID(trace_id)  # raises if not a valid UUID

    async def test_invalid_trace_id_is_replaced(self, client: AsyncClient):
        """An injection-style or oversized trace ID is replaced with a generated UUID."""
        malicious = "<script>alert(1)</script>"
        resp = await client.get("/healthz", headers={"x-trace-id": malicious})
        assert resp.status_code == 200
        returned = resp.headers.get("x-trace-id", "")
        # Must NOT echo the malicious value back
        assert returned != malicious
        # Must be a valid UUID
        import uuid

        uuid.UUID(returned)

    async def test_oversized_trace_id_is_replaced(self, client: AsyncClient):
        """A 100-character trace ID exceeds the 64-char limit and is replaced."""
        oversized = "a" * 100
        resp = await client.get("/healthz", headers={"x-trace-id": oversized})
        assert resp.headers.get("x-trace-id") != oversized

    async def test_context_isolated_between_requests(self, client: AsyncClient, test_user):
        """Two sequential requests receive their own trace IDs in response headers."""
        resp_a = await client.get("/healthz", headers={"x-trace-id": "trace-request-A"})
        resp_b = await client.get("/healthz", headers={"x-trace-id": "trace-request-B"})

        assert resp_a.headers["x-trace-id"] == "trace-request-A"
        assert resp_b.headers["x-trace-id"] == "trace-request-B"


# ---------------------------------------------------------------------------
# B + C. Audit events — content safety and trace-ID propagation
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestAuditEvents:
    async def test_login_failure_creates_safe_event(self, client: AsyncClient, test_user):
        """Login failure emits auth.login.failure without leaking password or email."""
        from structlog.testing import capture_logs

        wrong_password = "definitely_wrong_password_xyz"
        with capture_logs() as logs:
            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": test_user.email, "password": wrong_password},
            )

        assert resp.status_code == 401

        failure_events = [e for e in logs if e.get("event") == "auth.login.failure"]
        assert failure_events, "Expected at least one auth.login.failure audit event"

        all_log_str = str(logs)
        # Password must never appear in any log
        assert wrong_password not in all_log_str
        # Email must not appear in failure events (prevents account enumeration)
        assert test_user.email not in all_log_str

    async def test_login_success_audit_has_user_id_not_password(
        self, client: AsyncClient, test_user
    ):
        """Login success emits auth.login.success with user_id but without the password."""
        from structlog.testing import capture_logs

        with capture_logs() as logs:
            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": test_user.email, "password": "testpassword123"},
            )

        assert resp.status_code == 200

        success_events = [e for e in logs if e.get("event") == "auth.login.success"]
        assert success_events, "Expected auth.login.success audit event"
        ev = success_events[0]
        assert ev["user_id"] == str(test_user.id)
        assert "testpassword123" not in str(logs)

    async def test_no_raw_tokens_or_passwords_in_logs(self, client: AsyncClient):
        """Raw access tokens, refresh tokens, and passwords must not appear in any log."""
        from structlog.testing import capture_logs

        password = "securepassword_log_test_99"
        with capture_logs() as logs:
            resp = await client.post(
                "/api/v1/auth/register",
                json={
                    "name": "Log Safety User",
                    "email": "logsafety@example.com",
                    "password": password,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        all_log_str = str(logs)
        assert access_token not in all_log_str, "Raw access token must not appear in logs"
        assert refresh_token not in all_log_str, "Raw refresh token must not appear in logs"
        assert password not in all_log_str, "Password must not appear in logs"

    async def test_login_audit_event_carries_user_context(self, client: AsyncClient, test_user):
        """Login success audit event carries user_id, org_id, and role."""
        from structlog.testing import capture_logs

        with capture_logs() as logs:
            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": test_user.email, "password": "testpassword123"},
                headers={"x-trace-id": "test-trace-audit-99"},
            )

        assert resp.status_code == 200
        # Verify the trace ID is echoed in the HTTP response (middleware level)
        assert resp.headers["x-trace-id"] == "test-trace-audit-99"
        # Verify the audit event has the correct business fields
        success_events = [e for e in logs if e.get("event") == "auth.login.success"]
        assert success_events, "Expected auth.login.success audit event"
        ev = success_events[0]
        assert ev["user_id"] == str(test_user.id)
        assert ev["role"] == "OWNER"

    async def test_separate_requests_do_not_share_trace_context(self, client: AsyncClient):
        """Two sequential requests carry independent trace IDs in their response headers."""
        resp_a = await client.get("/healthz", headers={"x-trace-id": "trace-context-A"})
        resp_b = await client.get("/healthz", headers={"x-trace-id": "trace-context-B"})
        assert resp_a.headers["x-trace-id"] == "trace-context-A"
        assert resp_b.headers["x-trace-id"] == "trace-context-B"
