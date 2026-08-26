# apps/backend/Dockerfile
#
# Multi-stage build with four stages:
#   deps        — installs Python dependencies from the lock file
#   build       — assembles application files alongside the virtualenv
#   production  — minimal runtime image, non-root user, no hot reload (default target)
#   development — extends production, adds hot reload for local Compose

# ── Stage 1: resolve and install Python dependencies from lock file ──────────
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS deps
WORKDIR /app
COPY pyproject.toml uv.lock ./
# --frozen enforces the lock file; --no-dev omits test/lint tools
#RUN uv sync --frozen --no-dev
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: assemble only the runtime files needed in the container ─────────
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS build
WORKDIR /app
COPY --from=deps /app/.venv ./.venv
COPY alembic.ini ./
COPY migrations migrations/
COPY app app/

# ── Stage 3: production runtime ───────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS production
WORKDIR /app
# Create a non-root system user; prevents privilege escalation if the app is
# ever compromised.
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser
COPY --from=build --chown=appuser:appgroup /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
EXPOSE 8000
USER appuser
# Health check mirrors the Compose-level check so Docker Desktop shows status.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" \
    || exit 1
# WEB_CONCURRENCY controls the number of uvicorn worker processes.
# Set to 1 for single-CPU containers; scale up proportionally with CPU cores
# and remember to multiply DB_POOL_SIZE by the number of workers.
ENV WEB_CONCURRENCY=2
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY}"]

# ── Stage 4: development (hot reload, root user for bind-mount compatibility) ─
FROM production AS development
USER root
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
