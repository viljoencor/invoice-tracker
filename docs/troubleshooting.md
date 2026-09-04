# Troubleshooting Guide

Common issues and their solutions when running or developing Invoice Tracker.

---

## Table of Contents

1. [Application won't start / crashes immediately](#1-application-wont-start--crashes-immediately)
2. [Database not ready / connection refused](#2-database-not-ready--connection-refused)
3. [Alembic migration errors](#3-alembic-migration-errors)
4. [Login fails / tokens not working](#4-login-fails--tokens-not-working)
5. [Frontend CSP violations](#5-frontend-csp-violations)
6. [Full-stack / E2E test failures](#6-full-stack--e2e-test-failures)
7. [Cookie or auth-loop issues](#7-cookie-or-auth-loop-issues)
8. [PDF generation failures](#8-pdf-generation-failures)
9. [CI/CD pipeline failures](#9-cicd-pipeline-failures)
10. [Refresh token table growth](#10-refresh-token-table-growth)
11. [Rancher Desktop: `docker` not found or daemon won't connect](#11-rancher-desktop-docker-not-found-or-daemon-wont-connect)

---

## 1. Application won't start / crashes immediately

### Symptom
Backend exits immediately with a `ValidationError` or `ValueError: JWT_SECRET must be at least 32 characters`.

### Cause
`JWT_SECRET` is not set, is too short, or is a placeholder like `changeme`.

### Fix
Generate a strong secret:
```bash
openssl rand -hex 32
# Example output: 4a8f3c2d1b9e7f6a5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2
```
Set it in your `.env` file:
```
JWT_SECRET=4a8f3c2d1b9e7f6a5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2
```

The minimum length is 32 characters; production should use 64+.

---

## 2. Database not ready / connection refused

### Symptom
Backend logs show `connection refused` or `asyncpg.exceptions.ConnectionRefusedError` at startup, or:
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

### Cause
The PostgreSQL container is not yet ready when the backend starts. Docker Compose healthchecks require the database to be in the `healthy` state before the backend starts (configured in `docker-compose.yml`). If you see this error it usually means:

1. The healthcheck configuration is missing or incorrect
2. Docker Compose was started without `--wait` and you connected too quickly
3. The database image was pulled but the data directory is initializing for the first time

### Fix
1. **Wait for the database to become healthy**:
   ```bash
   docker compose up -d
   docker compose ps   # check "Status" column — db should show "(healthy)"
   ```
2. **Check PostgreSQL logs**:
   ```bash
   docker compose logs db
   ```
3. **Force restart with fresh state** (development only — destroys data):
   ```bash
   docker compose down -v   # removes volumes
   docker compose up -d
   ```

### Backend retry behaviour
The backend uses SQLAlchemy connection pool with `pool_pre_ping=True` and exponential-backoff retry logic (configurable via `DB_POOL_SIZE`, `DB_POOL_RECYCLE`). If the database becomes available within ~30 seconds the backend will reconnect automatically without restarting.

---

## 3. Alembic migration errors

### Symptom A: `FAILED: Can't locate revision identified by '...'`
The migration chain is broken. A revision references a `down_revision` that doesn't exist.

**Do not delete the empty `8cf5269df348_latest` migration.** It is a required no-op artefact in the chain:
```
b6c2545a61ef_init
  └── 8cf5269df348_latest   ← empty no-op, must exist
        └── a1b2c3d4e5f6_add_refresh_tokens
```

### Symptom B: `ERROR [alembic.runtime.migration] Table 'users' already exists`
Running `alembic upgrade head` against a database that already has the schema but no `alembic_version` table (e.g. from a pre-Alembic seed).

**Fix**:
```bash
# Stamp the database at the current head without running migrations
docker compose exec backend alembic stamp head
# Now future upgrades will work normally
```

### Symptom C: `Multiple heads are present`
Two branches in the migration tree that were not merged.

**Fix**:
```bash
cd apps/backend
uv run alembic heads          # list both heads
uv run alembic merge heads    # auto-creates a merge revision
uv run alembic upgrade head
```

### Symptom D: Migration runs but schema doesn't change
The revision file has an empty `upgrade()` function or `pass`. This is intentional for `8cf5269df348_latest` (historical artefact). If you created a new migration that is unexpectedly empty, Alembic could not detect any schema changes — usually because:
- The model changes weren't imported in `migrations/env.py`
- The model was imported after Alembic compared the metadata

Check that all models are imported before `target_metadata = Base.metadata` in `migrations/env.py`.

---

## 4. Login fails / tokens not working

### Symptom
Login endpoint returns `401 Unauthorized` even with correct credentials.

### Cause A: Wrong password
The seed script (`python -m app.scripts.seed`) creates `admin@example.com` with password `admin123`. The password is hashed with Argon2; the hash changes each time the seed runs.

### Cause B: Database was wiped but the seed wasn't re-run
```bash
docker compose exec backend python -m app.scripts.seed
```

### Cause C: `JWT_SECRET` changed between deployments
All previously issued tokens are invalidated. All users must log in again. This is expected — not a bug.

### Symptom: `422 Unprocessable Entity` on login
The request body schema is wrong. The login endpoint expects `username` and `password` fields (OAuth2 form schema), not `email`.

---

## 5. Frontend CSP violations

### Symptom
Browser console shows `Content Security Policy: The page's settings blocked the loading of a resource`.

### Common violations and fixes

| Violation | Cause | Fix |
|---|---|---|
| `connect-src` blocked API calls | BFF proxy URL not in `connect-src` | The CSP `connect-src 'self'` allows same-origin calls to `/api/proxy/*`; if you're calling an external URL directly, add it to `connect-src` in `server/middleware/01.security-headers.ts` |
| `style-src` blocked Tailwind inline styles | Tailwind v3 generates inline `<style>` blocks | `style-src 'self' 'unsafe-inline'` is set by default; verify it's present |
| `script-src` blocked chunk | Dynamic chunk URL hashed differently | Add a nonce or extend `script-src` — this is rare with Nuxt's asset manifest |
| `frame-ancestors` blocked iframe | `X-Frame-Options: DENY` + `frame-ancestors 'none'` | Intentional; the app cannot be embedded in an iframe |

### Viewing active CSP
Check the `Content-Security-Policy` response header on any page request in DevTools → Network → select a document request → Headers.

---

## 6. Full-stack / E2E test failures

### Symptom
Playwright tests fail with `page.goto` timeout or element not found.

### Cause A: Stack not running
```bash
cd infra && docker compose ps   # all services must be "Up (healthy)"
```

### Cause B: Seed not run / wrong credentials
```bash
docker compose exec backend python -m app.scripts.seed
```
Then set env vars for E2E:
```bash
export E2E_TEST_EMAIL=admin@example.com
export E2E_TEST_PASSWORD=admin123
```

### Cause C: `valid credentials` test is skipped
This is **expected** when `E2E_TEST_PASSWORD` is not set. The test has a built-in skip guard.

### Cause D: Polling timeout in CI
The CI integration job uses a polling loop to wait for the stack to become ready:
```yaml
until curl -sf http://localhost:8000/healthz; do sleep 2; done
```
If the healthcheck takes longer than 60s (the loop limit), the job fails. Common causes:
- Database taking too long to initialize (cold Docker layer cache)
- Backend not starting (check `docker compose logs backend`)

### Cause E: Screenshot/video on failure
Playwright is configured with `screenshot: 'only-on-failure'` and `video: 'retain-on-failure'`. Check the `playwright-report/` directory after a failed run for visual evidence.

---

## 7. Cookie or auth-loop issues

### Symptom
After login, the user is immediately redirected back to `/login`, or the app loops between login and dashboard.

### Cause A: `session` cookie not set (domain mismatch)
The `session` cookie is set by the BFF (`/api/auth/login`). If the frontend is accessed on a different hostname than where the BFF sets the cookie, the browser may not send it back.

In development, access the app on `http://localhost:3000` exactly (not `127.0.0.1:3000`).

### Cause B: `secure` flag on non-HTTPS connection
In production (`ENVIRONMENT=production`), cookies are set with `Secure: true`. If the browser accesses the app over plain HTTP (not HTTPS), the cookie is not stored.

Ensure Nginx is configured with SSL and the app is accessed via `https://`.

### Cause C: `SameSite=Lax` and cross-origin form post
If the login form is somehow served from a different origin than the BFF, `SameSite=Lax` will block the cookie from being sent on the initial POST. This should not happen in normal operation (same-origin SPA).

### Cause D: BFF can't reach FastAPI (`NUXT_API_BASE` wrong)
The BFF reads `NUXT_API_BASE` (private, server-side only). If this is misconfigured, login will return `500` instead of setting cookies.

Check that:
```
# In docker-compose.yml / .env
NUXT_API_BASE=http://backend:8000/api/v1   # internal Docker network name
```

Note: `NUXT_PUBLIC_API_BASE` is **not** used. The variable is `NUXT_API_BASE` (no `PUBLIC`).

### Symptom: Infinite refresh loop
The BFF attempts to refresh on `401` from FastAPI. If the refresh endpoint itself returns `401`, the BFF clears cookies and returns `401` to the browser — which should redirect to `/login`. If the redirect isn't happening:

Check `apps/frontend/middleware/auth.ts` — it reads the `session` cookie. If `session=1` is still set after a failed refresh (a bug), the middleware won't redirect. This should not happen as `clearAuthCookies` removes all three cookies atomically.

---

## 8. PDF generation failures

### Symptom
`GET /api/v1/invoices/{id}/pdf` returns `500 Internal Server Error`.

### Cause A: ReportLab not installed
```bash
docker compose exec backend pip show reportlab
# or
cd apps/backend && uv run python -c "import reportlab; print(reportlab.__version__)"
```

### Cause B: Invoice has no line items
The PDF service requires at least one `InvoiceItem`. An invoice with zero items may cause a division error or empty table. Check the invoice data:
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/invoices/<id>
```

### Cause C: Permission denied on temp directory
The PDF is generated in memory (BytesIO) and should not require a temp directory. If you see a `PermissionError`, check that the backend container has a writable `/tmp`.

---

## 9. CI/CD pipeline failures

### Symptom: `backend-quality` job fails on `mypy`
Run locally:
```bash
cd apps/backend && uv run mypy app
```
Common causes: missing `Optional` annotation, untyped third-party library (add to `[[tool.mypy.overrides]]` in `pyproject.toml`).

### Symptom: `frontend-quality` job fails on `typecheck`
```bash
cd apps/frontend && npm run typecheck
```
Common causes: Vue component prop types changed, missing import, Nuxt auto-import type not resolved.

### Symptom: `publish` job fails with `denied: permission_denied`
The `GITHUB_TOKEN` in Actions needs `packages: write` permission. Check:
```yaml
# .github/workflows/ci.yml
permissions:
  contents: read
  packages: write
```
Also ensure the repository owner matches the GHCR image path (`ghcr.io/OWNER/...`).

### Symptom: Coverage gate fails (`--cov-fail-under=70`)
Current actual coverage is **~89%** (well above the 70% threshold). If coverage drops below 70%, add tests for the newly added code before merging. Note that `[tool.coverage.run]` sets `concurrency = ["greenlet", "thread"]` — this is required for coverage.py to correctly attribute lines executed through SQLAlchemy's async ORM; removing it will silently undercount router coverage without failing the gate.

Frontend coverage thresholds are in `apps/frontend/vitest.config.ts` (50% lines/statements/functions, 40% branches). The `coverage.include` list covers `pages/**` and `server/api/**` in addition to composables/components/middleware/stores/server-utils — keep new server routes and pages inside this scope so regressions there are actually measured.

---

## 10. Refresh token table growth

### Symptom
The `refresh_tokens` table grows steadily over time even though users log out normally.

### Cause
Login/refresh/logout only ever mark a row `revoked = true`; nothing deletes old rows automatically apart from an opportunistic cleanup of the *current user's* own expired/revoked tokens at login time.

### Fix
Run the cleanup script periodically (cron / scheduled task) to delete revoked or expired rows for all users:
```bash
cd apps/backend
python -m app.scripts.cleanup_tokens
```
This is safe to run at any time — it only ever deletes rows that are already `revoked = true` or past `expires_at`.

---

## 11. Rancher Desktop: `docker` not found or daemon won't connect

This project's Compose setup (`infra/docker-compose.yml`) works with **Rancher Desktop** as a drop-in replacement for Docker Desktop, but two Rancher-specific gotchas are easy to hit on first install.

### Symptom A: `docker : The term 'docker' is not recognized...`

### Cause
Rancher Desktop's installer adds its CLI directory (`...\Rancher Desktop\resources\resources\win32\bin`) to your **User** PATH, but any terminal window opened *before* installation finished still has the old PATH cached in memory.

### Fix
Close and reopen your terminal (or restart VS Code) so it picks up the updated PATH, then verify:
```powershell
docker --version
docker compose version
```

### Symptom B: `failed to connect to the docker API at npipe:////./pipe/docker_engine`

### Cause
Rancher Desktop's background log (`%LOCALAPPDATA%\rancher-desktop\logs\background.log`) shows the real failure, typically something like:
```
Rancher Desktop was unable to start: FetchError: request to https://127.0.0.1:6443/api/v1/nodes failed, reason: read ECONNRESET
```
By default Rancher Desktop also starts a Kubernetes (k3s) cluster and ties the container-engine startup to the Kubernetes startup sequence. If k3s fails to come up (resource limits, WSL networking hiccups, first-run timing), the container engine — and the named pipe `docker` needs — never gets created either. This project's Compose file does not use Kubernetes at all.

### Fix
1. Open the Rancher Desktop app → **Preferences → Kubernetes** → uncheck **Enable Kubernetes** → **Apply**.
2. Under **Preferences → Container Engine**, select **dockerd (moby)** (most directly compatible with plain `docker compose`; containerd + `nerdctl` also works but isn't necessary here).
3. Wait for the Rancher Desktop window to show a green **Running** status.
4. Open a **new** terminal and confirm:
   ```powershell
   docker info
   ```
   Once this returns without error, the Quick Start steps in the main [README](../README.md#run-the-application-docker) work unmodified.
