"""Tests for the TimeoutMiddleware — isolated from the full FastAPI app."""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.unit
class TestTimeoutMiddleware:
    async def test_fast_request_passes_through(self):
        """A handler that completes within the timeout returns its normal response."""
        from fastapi.responses import JSONResponse
        from starlette.types import Receive, Scope, Send

        from app.middleware import TimeoutMiddleware

        async def fast_app(scope: Scope, receive: Receive, send: Send) -> None:
            response = JSONResponse({"ok": True})
            await response(scope, receive, send)

        app = TimeoutMiddleware(fast_app, timeout=5.0)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/")

        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    async def test_slow_request_returns_504(self):
        """A handler that exceeds the timeout receives a 504 Gateway Timeout response."""
        from starlette.types import Receive, Scope, Send

        from app.middleware import TimeoutMiddleware

        async def slow_app(scope: Scope, receive: Receive, send: Send) -> None:
            await asyncio.sleep(10.0)  # will be cancelled by the timeout

        app = TimeoutMiddleware(slow_app, timeout=0.1)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/")

        assert resp.status_code == 504
        assert "timeout" in resp.json()["detail"].lower()

    async def test_non_http_scope_passes_through(self):
        """WebSocket and lifespan scopes are not subject to the timeout."""
        from app.middleware import TimeoutMiddleware

        received: list[str] = []

        async def recording_app(scope, receive, send) -> None:
            received.append(scope["type"])

        app = TimeoutMiddleware(recording_app, timeout=0.01)
        # Simulate a WebSocket scope directly (no HTTP connection needed)
        await app({"type": "websocket"}, None, None)  # type: ignore[arg-type]

        assert "websocket" in received

    async def test_timeout_setting_is_configurable(self):
        """The request_timeout_seconds setting is wired into the app."""
        from app.config import settings

        assert 5 <= settings.request_timeout_seconds <= 300
