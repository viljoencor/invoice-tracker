import re
import uuid

import structlog
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

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
