import re
import uuid

import anyio
import structlog
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

# Accept only safe trace IDs: alphanumeric, hyphens, underscores, 1–64 chars.
# Rejects injections like "<script>...</script>" or unbounded-length strings.
_TRACE_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Clear any leftover context from the previous request on this worker
        structlog.contextvars.clear_contextvars()

        # Use the inbound trace ID only if it passes format validation
        raw = request.headers.get("x-trace-id", "")
        trace_id = raw if _TRACE_ID_RE.match(raw) else str(uuid.uuid4())

        # Bind trace_id so every structlog call during this request carries it
        structlog.contextvars.bind_contextvars(trace_id=trace_id)

        try:
            response: Response = await call_next(request)
        finally:
            # Always clear — covers normal completion and exception paths
            structlog.contextvars.clear_contextvars()

        response.headers["x-trace-id"] = trace_id
        return response


# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


class TimeoutMiddleware:
    """
    Pure-ASGI middleware that enforces a per-request processing deadline.

    Returns HTTP 504 when the application does not complete within ``timeout``
    seconds.  Only applied to HTTP scopes; WebSocket and lifespan scopes are
    passed through unmodified.

    Safety note: when a timeout fires mid-transaction the underlying async
    session's context manager rolls back the transaction before releasing the
    connection.  Payment idempotency keys prevent double-charging on retries.

    Infrastructure timeout layers (for reference):
    - Nginx proxy_read_timeout (currently 60 s) — reverse-proxy deadline
    - This middleware (default 55 s) — application deadline (fires first)
    - Uvicorn --timeout-graceful-shutdown — worker shutdown grace period
    - DB statement timeout — set via DATABASE_URL or session option if needed
    """

    def __init__(self, app: ASGIApp, timeout: float) -> None:
        self.app = app
        self.timeout = timeout

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def _send(message: dict) -> None:  # type: ignore[type-arg]
            nonlocal response_started
            if message.get("type") == "http.response.start":
                response_started = True
            await send(message)

        try:
            with anyio.fail_after(self.timeout):
                await self.app(scope, receive, _send)  # type: ignore[arg-type]
        except TimeoutError:
            if not response_started:
                response = JSONResponse(
                    status_code=504,
                    content={"detail": "Request timeout"},
                )
                await response(scope, receive, send)
