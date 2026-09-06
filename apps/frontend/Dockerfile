# apps/frontend/Dockerfile
#
# Multi-stage Nuxt build:
#
#   deps        - installs dependencies
#   build       - builds the Nuxt/Nitro application
#   production  - minimal runtime, no npm tooling
#   development - development server with hot reload


# ============================================================================
# Stage 1: Install dependencies
# ============================================================================

FROM node:22.22.2-alpine3.23 AS deps

WORKDIR /app

COPY package.json package-lock.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-fund


# ============================================================================
# Stage 2: Build the Nuxt application
# ============================================================================

FROM deps AS build

WORKDIR /app

COPY . .

RUN npm run build


# ============================================================================
# Stage 3: Production
#
# Nuxt/Nitro does not need npm at runtime.
#
# The application runs directly with:
#
#   node .output/server/index.mjs
#
# npm is deliberately removed because the Node base image currently ships an
# npm dependency containing vulnerable tar@6.2.1 (CVE-2026-59873).
# ============================================================================

FROM node:22.22.2-alpine3.23 AS production

WORKDIR /app


# ---------------------------------------------------------------------------
# Apply available Alpine security patches.
# ---------------------------------------------------------------------------

RUN apk upgrade --no-cache


# ---------------------------------------------------------------------------
# Remove npm and npx from the production image.
#
# They are build tooling and are not required by the Nitro runtime.
#
# This also removes:
#
#   /usr/local/lib/node_modules/npm/node_modules/tar
#
# which is the package currently causing the CRITICAL Trivy failure.
# ---------------------------------------------------------------------------

RUN rm -rf /usr/local/lib/node_modules/npm \
    && rm -f /usr/local/bin/npm \
    && rm -f /usr/local/bin/npx


# ---------------------------------------------------------------------------
# Create non-root application user.
# ---------------------------------------------------------------------------

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser


# ---------------------------------------------------------------------------
# Copy only the compiled Nitro production output.
#
# node_modules from the build environment are NOT copied.
# ---------------------------------------------------------------------------

COPY --from=build \
    --chown=appuser:appgroup \
    /app/.output \
    ./.output


# ---------------------------------------------------------------------------
# Runtime configuration.
# ---------------------------------------------------------------------------

ENV NODE_ENV=production \
    NITRO_HOST=0.0.0.0 \
    NITRO_PORT=3000

EXPOSE 3000


# ---------------------------------------------------------------------------
# Run as non-root.
# ---------------------------------------------------------------------------

USER appuser


# ---------------------------------------------------------------------------
# Production health check.
#
# Alpine provides wget through BusyBox, so we do not install another package
# purely for health checking.
# ---------------------------------------------------------------------------

HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=40s \
    --retries=3 \
    CMD wget -q --spider http://localhost:3000 || exit 1


# ---------------------------------------------------------------------------
# Start Nitro directly.
#
# npm is intentionally not available in the production image.
# ---------------------------------------------------------------------------

CMD ["node", ".output/server/index.mjs"]


# ============================================================================
# Stage 4: Development
#
# Development extends the deps stage because npm is required here.
# ============================================================================

FROM deps AS development

WORKDIR /app

COPY . .

ENV NODE_ENV=development \
    HOST=0.0.0.0 \
    PORT=3000

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]