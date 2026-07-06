# ── Stage 1: Install dependencies ────────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund

# ── Stage 2: Build the Nuxt app ───────────────────────────────────────────────
FROM deps AS build
COPY . .
RUN npm run build

# ── Stage 3: Production (Nitro server, non-root user) ─────────────────────────
FROM node:20-alpine AS production
WORKDIR /app
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
COPY --from=build --chown=appuser:appgroup /app/.output ./.output
ENV NODE_ENV=production
ENV NITRO_PORT=3000
EXPOSE 3000
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget -q --spider http://localhost:3000 || exit 1
CMD ["node", ".output/server/index.mjs"]

# ── Stage 4: Development (hot reload) ─────────────────────────────────────────
FROM deps AS development
COPY . .
ENV NITRO_PORT=3000
EXPOSE 3000
CMD ["npm", "run", "dev"]
