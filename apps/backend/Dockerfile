# apps/backend/Dockerfile
#
# Multi-stage build:
#   deps        - installs locked Python runtime dependencies
#   build       - assembles application + virtual environment
#   production  - minimal Python runtime only
#   development - production image with hot reload enabled


# ============================================================================
# Stage 1: Dependencies
# ============================================================================

FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS deps

WORKDIR /app

COPY pyproject.toml uv.lock ./

# Install only production dependencies.
# --frozen ensures uv.lock is authoritative.
# --no-install-project avoids installing the application package itself.
RUN uv sync \
    --frozen \
    --no-dev \
    --no-install-project


# ============================================================================
# Stage 2: Build
# ============================================================================

FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS build

WORKDIR /app

COPY --from=deps /app/.venv ./.venv

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app


# ============================================================================
# Stage 3: Production
#
# IMPORTANT:
# Do NOT use the Astral uv image here.
#
# The uv image contains build/development tooling and a much larger Debian
# package set than the application needs at runtime.
#
# A minimal Python slim image substantially reduces the attack surface and
# removes packages such as ImageMagick that caused the Trivy findings.
# ============================================================================

FROM python:3.12-slim-bookworm AS production

WORKDIR /app


# ---------------------------------------------------------------------------
# Patch the Debian runtime layer
#
# The base image can contain Debian packages that have received security
# updates since the image layer was published.
# ---------------------------------------------------------------------------

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*


# ---------------------------------------------------------------------------
# Create non-root runtime user
# ---------------------------------------------------------------------------

RUN groupadd --system appgroup \
    && useradd \
        --system \
        --gid appgroup \
        --home-dir /app \
        --no-create-home \
        appuser


# ---------------------------------------------------------------------------
# Copy application and virtual environment
# ---------------------------------------------------------------------------

COPY --from=build --chown=appuser:appgroup /app /app


# ---------------------------------------------------------------------------
# Runtime configuration
# ---------------------------------------------------------------------------

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WEB_CONCURRENCY=2


EXPOSE 8000


# ---------------------------------------------------------------------------
# Run as non-root
# ---------------------------------------------------------------------------

USER appuser


# ---------------------------------------------------------------------------
# Health check
#
# urllib.request is part of the Python standard library, so curl/wget is not
# required in the production image.
# ---------------------------------------------------------------------------

HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=40s \
    --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY}"]


# ============================================================================
# Stage 4: Development
#
# Extends the production runtime but runs as root for local bind-mounted
# development.
# ============================================================================

FROM production AS development

USER root

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]