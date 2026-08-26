# Invoice Tracker

A production-ready full-stack invoice management system with multi-tenant architecture, designed for small businesses to track invoices, clients, and payments.

## What It Does

Invoice Tracker is a complete billing solution that enables organizations to:
- **Manage Clients**: Create, view, edit, and delete client records
- **Generate Invoices**: Create itemized invoices with line items, automatic totals, and PDF export
- **Track Payments**: Record payments with idempotency protection; invoice status updates automatically
- **Generate PDFs**: Export professional invoice PDFs via the server-side ReportLab service
- **Dashboard Analytics**: Revenue trend chart and key performance indicators (KPI cards)
- **Multi-Tenant Support**: All data is strictly isolated per organization

## Architecture & Design

### Technology Stack

**Frontend**: Nuxt 3.12 (SPA mode, `ssr: false`), Nitro BFF proxy, TailwindCSS, TypeScript, Vitest, Playwright  
**Backend**: FastAPI (async), SQLAlchemy 2.0 (async ORM), Pydantic v2, Alembic migrations  
**Database**: PostgreSQL 16  
**Authentication**: JWT (HS256) + refresh-token rotation, Argon2 password hashing, httpOnly cookies, CSRF protection  
**PDF Generation**: ReportLab via a service adapter  
**Infrastructure**: Docker Compose (dev / staging / prod), Nginx reverse proxy, GitHub Actions CI/CD, GHCR image registry

### Auth & Security Architecture (Phase 8 BFF)

All browser requests go to the Nitro BFF proxy (`/api/proxy/*`) — the browser never contacts FastAPI directly.

```
Browser
  │  POST /api/auth/login        (credentials)
  │  POST /api/auth/logout
  │  POST /api/auth/refresh
  │  GET|POST|PATCH|DELETE /api/proxy/**
  ▼
Nitro BFF (same origin — port 3000)
  │  httpOnly cookies: at (access token), rt (refresh token)
  │  Non-httpOnly cookie: session=1 (auth indicator for client JS)
  │  CSRF: Origin ↔ Host header validation for state-changing methods
  │  Security headers: CSP, X-Frame-Options, X-Content-Type-Options, …
  │
  │  Bearer <at>  →  FastAPI (http://backend:8000/api/v1)
  ▼
FastAPI  →  PostgreSQL
```

On 401 from FastAPI the BFF transparently rotates tokens and retries once. If both tokens are expired, cookies are cleared and 401 is returned to the browser, triggering a redirect to `/login`.

### Data Model

**Organizations** → Multi-tenant isolation root  
**Users** → Authentication, belongs to Organization  
**Clients** → Customer records, scoped by Organization  
**Invoices** → Billing documents with status tracking (`draft` / `sent` / `paid` / `partially_paid`)  
**InvoiceItems** → Line items with qty, unit price (cents), tax rate (basis points)  
**Payments** → Payment records linked to invoices (idempotent via `Idempotency-Key`)  
**RefreshTokens** → Hashed refresh tokens with revocation support

All monetary values stored as **integer cents** to avoid floating-point precision issues.  
All queries are **organization-scoped** (every table carries `org_id`).  
Concurrent payments are protected by **`SELECT … FOR UPDATE`** row-level locking.

## Project Structure

```
invoice-tracker/
├── .github/workflows/
│   ├── ci.yml           # Full CI pipeline (quality → integration/E2E → publish)
│   └── release.yml      # Manual release workflow (promotes SHA tag to environment)
├── apps/
│   ├── backend/              # FastAPI application
│   │   ├── app/
│   │   │   ├── main.py       # App entry, middleware, error handlers
│   │   │   ├── models.py     # SQLAlchemy ORM models
│   │   │   ├── schemas.py    # Pydantic request/response schemas
│   │   │   ├── security.py   # JWT & password utilities
│   │   │   ├── db.py         # Database connection & pooling
│   │   │   ├── config.py     # Settings management
│   │   │   ├── routers/      # API endpoints (auth, invoices, clients, payments, dash)
│   │   │   └── services/     # Business logic (PDF generation)
│   │   ├── migrations/       # Alembic database migrations (3 revisions)
│   │   ├── tests/            # Pytest suite (81 tests, 74% coverage)
│   │   └── pyproject.toml    # Python dependencies (uv)
│   └── frontend/             # Nuxt 3 application
│       ├── server/           # Nitro BFF (auth endpoints, proxy, CSRF, security headers)
│       ├── pages/            # Route components (dashboard, invoices, clients, login)
│       ├── components/       # KpiCard, RevenueChart, AppErrorBoundary
│       ├── composables/      # useApi (proxy client), useAuth (session indicator)
│       ├── middleware/       # Route guard (session cookie check)
│       ├── layouts/          # default.vue (nav + error boundary)
│       └── tests/            # Vitest (87 unit tests) + Playwright E2E
├── docs/
│   ├── adr/             # Architecture Decision Records
│   └── troubleshooting.md
├── infra/
│   ├── docker-compose.yml           # Development environment
│   ├── docker-compose.staging.yml   # Staging environment
│   ├── docker-compose.prod.yml      # Production environment
│   ├── .env.staging.example         # Staging variable template
│   ├── .env.prod.example            # Production variable template
│   └── nginx/nginx.conf             # Reverse proxy config
└── scripts/
    └── run-checks.py         # Backend quality checks runner
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- For local backend development: Python 3.12+, `uv`
- For local frontend development: Node.js 20+

### Run the Application (Docker)

```bash
# 1. Clone and navigate
git clone https://github.com/viljoencor/invoice-tracker
cd invoice-tracker

# 2. Start all services (database, backend, frontend)
cd infra
docker compose up --build -d

# 3. Run database migrations (first-time and after code updates)
docker compose exec backend alembic upgrade head

# 4. Seed demo data (optional — creates admin@example.com / admin123)
docker compose exec backend python -m app.scripts.seed

# 5. Access the application
# Frontend:  http://localhost:3000
# API Docs:  http://localhost:8000/docs
# Health:    http://localhost:8000/healthz
```

**Demo credentials**: `admin@example.com` / `admin123` (seed script only — not hardcoded in the login form)

### Local Backend Development

```bash
cd apps/backend
uv sync --all-extras --dev   # Install dependencies including dev tools
uv run pytest                # Run tests (SQLite in-memory, no Docker needed)
uv run pytest --cov          # Run tests with coverage (threshold: 50%)
uv run uvicorn app.main:app --reload  # Dev server (requires running PostgreSQL)
```

### Local Frontend Development

```bash
cd apps/frontend
npm ci
npm run dev        # Dev server — requires the stack to be up for BFF to reach FastAPI
npm run typecheck  # vue-tsc --noEmit
npm test           # Vitest unit tests (no stack needed)
npm run test:coverage  # Unit tests + coverage report
```

## Testing

### Backend Tests

```bash
cd apps/backend
uv run pytest --cov --cov-report=term   # 81 tests, 74% coverage, threshold 50%
uv run pytest -m "not slow"             # Skip slow tests
```

### Frontend Unit Tests

```bash
cd apps/frontend
npm test                 # 87 tests, 0 failures
npm run test:coverage    # With coverage thresholds (≥50% lines/statements/functions, ≥40% branches)
```

### Full-Stack E2E Tests (Playwright)

E2E tests require the full stack to be running:

```bash
# Start the stack
cd infra && docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed

# Run Playwright tests
cd apps/frontend
E2E_TEST_EMAIL=admin@example.com E2E_TEST_PASSWORD=admin123 npm run test:e2e
```

The `valid credentials` E2E test is skipped automatically when `E2E_TEST_PASSWORD` is not set.

## Configuration

### Backend Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection (asyncpg) | Required |
| `JWT_SECRET` | JWT signing secret (≥32 chars) | Required in production |
| `ENVIRONMENT` | `development` / `staging` / `production` | `development` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | Refresh token lifetime | `720` |
| `DB_POOL_SIZE` | Connection pool size | `20` |
| `DB_MAX_OVERFLOW` | Max overflow connections | `10` |
| `DB_POOL_RECYCLE` | Pool recycle interval (seconds) | `3600` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |
| `RATE_LIMIT_PER_MINUTE` | Requests per minute per IP | `60` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `LOG_JSON_FORMAT` | JSON structured logging | `false` |

### Frontend Environment Variables

| Variable | Description | Default |
|---|---|---|
| `NUXT_API_BASE` | **Private** BFF→FastAPI URL (Nitro server only, not sent to browser) | `http://127.0.0.1:8000/api/v1` |
| `NODE_ENV` | Node environment | `development` |

> **Note**: There is no public `NUXT_PUBLIC_*` API variable. All browser API traffic flows through the Nitro BFF proxy at `/api/proxy/*`.

## Deployment

### Development

```bash
cd infra
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

### Staging

```bash
cd infra
cp .env.staging.example .env.staging
# Edit .env.staging with real values (generate secrets with: openssl rand -hex 32)
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d
# Run migrations before starting the app
docker compose -f docker-compose.staging.yml exec backend alembic upgrade head
```

### Production

```bash
cd infra
cp .env.prod.example .env.prod
# Fill in all required values
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

**Production checklist**:
- [ ] Generate `JWT_SECRET` with `openssl rand -hex 32` (minimum 32 chars)
- [ ] Use a strong `DB_PASSWORD`
- [ ] Set `ENVIRONMENT=production` (sanitizes error messages)
- [ ] Enable `LOG_JSON_FORMAT=true` for log aggregation
- [ ] Configure Nginx SSL certificates
- [ ] Set up database backups
- [ ] Use pinned immutable image tags (not `latest`) — see CI/CD section below

### CI/CD and Image Publishing

The GitHub Actions pipeline (`.github/workflows/ci.yml`) runs automatically on push:

1. **`backend-quality`** — Ruff lint + format, MyPy, Bandit, pytest (coverage ≥50%)
2. **`frontend-quality`** — vue-tsc typecheck, Vitest unit tests (coverage thresholds), Nuxt production build
3. **`integration`** — Full Docker Compose stack, migration cycle, seed, Playwright E2E
4. **`publish`** (main/master only) — Build production images, push to `ghcr.io/OWNER/invoice-tracker-{backend,frontend}:sha-COMMIT`, Trivy image scan with SBOM attestations

To promote a published image to staging or production use the **manual release workflow**:

```
GitHub → Actions → Release → Run workflow
  image_tag: sha-abc1234
  environment: staging | production
```

This re-tags the image and creates a GitHub Release with the deployment instructions.

## API Reference

All endpoints require a valid session (via the BFF proxy at `/api/proxy/*`) unless stated.  
The BFF injects the `Authorization: Bearer` header server-side — clients never handle tokens directly.

### Authentication (direct to BFF, not proxy)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Login — sets `at`, `rt`, `session` cookies |
| `POST` | `/api/auth/logout` | Logout — revokes refresh token, clears cookies |
| `POST` | `/api/auth/refresh` | Rotate tokens — called internally by BFF on 401 |

### FastAPI Endpoints (via BFF proxy at `/api/proxy/…`)

#### Auth
| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user + org |
| `POST` | `/auth/login` | Login — returns `TokenPair` (used internally by BFF) |
| `GET` | `/auth/me` | Get current user info |
| `POST` | `/auth/refresh` | Rotate access + refresh tokens (used internally by BFF) |
| `POST` | `/auth/logout` | Revoke refresh token (used internally by BFF) |

#### Clients
| Method | Path | Description |
|---|---|---|
| `GET` | `/clients` | List clients for org |
| `POST` | `/clients` | Create client |
| `GET` | `/clients/{id}` | Get client by ID |
| `PATCH` | `/clients/{id}` | Update client fields |
| `DELETE` | `/clients/{id}` | Delete client (blocks if active invoices exist) |

#### Invoices
| Method | Path | Description |
|---|---|---|
| `GET` | `/invoices` | List invoices (supports `status`, `client_id`, `sort`, `limit` filters) |
| `POST` | `/invoices` | Create invoice with line items |
| `GET` | `/invoices/{id}` | Get invoice detail (includes line items) |
| `GET` | `/invoices/{id}/pdf` | Download invoice as PDF |
| `POST` | `/invoices/{id}/send` | Mark invoice as sent (status: draft → sent) |
| `GET` | `/invoices/summary` | Aggregate counts and totals by status |

#### Payments
| Method | Path | Description |
|---|---|---|
| `GET` | `/payments` | List payments (supports `invoice_id` filter) |
| `POST` | `/payments` | Record payment (requires `Idempotency-Key` header) |

#### Dashboard
| Method | Path | Description |
|---|---|---|
| `GET` | `/dash/summary` | KPIs and revenue chart data for the dashboard |

## Notes

- All monetary amounts stored as **integer cents** (no floating-point rounding errors)
- All database queries are **organization-scoped** for multi-tenant isolation
- Frontend is an **SPA** (`ssr: false`) — Nitro server routes still run for the BFF
- Concurrent payment protection via **row-level locking** (`SELECT … FOR UPDATE`)
- **Idempotency-Key** header required on `POST /payments` to prevent duplicate charges
- JWT access tokens expire in 30 minutes; refresh tokens in 12 hours
- Database migrations managed with Alembic; always run `alembic upgrade head` before starting the app


## What It Does

Invoice Tracker is a complete billing solution that enables organizations to:
- **Manage Clients**: Create and maintain client records with contact information
- **Generate Invoices**: Create itemized invoices with line items and automatic total calculations
- **Track Payments**: Record and monitor payments against invoices with status tracking
- **Generate PDFs**: Export professional invoice PDFs for client delivery
- **Dashboard Analytics**: View revenue trends and key performance indicators
- **Multi-Tenant Support**: Isolated data per organization

![alt text](https://github.com/viljoencor/invoice-tracker/blob/master/apps/frontend/assets/invoicer.jpg?raw=true)

## Architecture & Design

### Technology Stack

**Frontend**: Nuxt 3 (Vue 3), Pinia (state management), TailwindCSS, TypeScript  
**Backend**: FastAPI (async), SQLAlchemy 2.0 (async ORM), Pydantic v2 (validation)  
**Database**: PostgreSQL 16 with Alembic migrations  
**Authentication**: JWT (HS256) with access/refresh tokens, Argon2 password hashing  
**PDF Generation**: ReportLab with service adapter pattern  
**Infrastructure**: Docker Compose, Nginx reverse proxy

### System Architecture

```
┌─────────────────┐
│   Nuxt 3 SPA    │  → Client-side rendering, reactive UI
│   (Port 3000)   │     State management with Pinia
└────────┬────────┘
         │ HTTP/REST
         ↓
┌─────────────────┐
│  Nginx Proxy    │  → Rate limiting, SSL termination
│   (Production)  │     Request routing
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  FastAPI API    │  → Async request handling
│   (Port 8000)   │     JWT authentication
│                 │     Business logic & validation
└────────┬────────┘
         │ asyncpg
         ↓
┌─────────────────┐
│  PostgreSQL 16  │  → Relational data storage
│   (Port 5432)   │     ACID transactions
└─────────────────┘
```

### Data Model

**Organizations** → Multi-tenant isolation root  
**Users** → Authentication, belongs to Organization  
**Clients** → Customer records, scoped by Organization  
**Invoices** → Billing documents with status tracking (draft/sent/paid)  
**InvoiceItems** → Line items with qty, rate, amount  
**Payments** → Payment records linked to Invoices

All monetary values stored as integer cents to avoid floating-point precision issues. All queries are organization-scoped for data isolation.

### Security Features

- JWT token authentication with secure refresh mechanism
- Rate limiting on authentication endpoints (60 req/min)
- Strong secret validation (32+ character minimum in production)
- Password hashing with Argon2 (memory-hard algorithm)
- CORS configuration for cross-origin protection
- SQL injection prevention via SQLAlchemy ORM
- Automated security scanning (Bandit, Trivy)

### Production Features

- **Database**: Connection pooling (20 connections), automatic retry with exponential backoff
- **Monitoring**: Health check endpoints (`/healthz`, `/readiness`), structured JSON logging
- **Error Handling**: Global exception handling with sanitized production errors
- **Performance**: Async I/O throughout, database query optimization
- **Testing**: >80% code coverage with unit, integration, and E2E tests
- **CI/CD**: Automated linting (Ruff), type checking (MyPy), security scanning

## Project Structure

```
invoice-tracker/
├── apps/
│   ├── backend/              # FastAPI application
│   │   ├── app/
│   │   │   ├── main.py       # App entry, middleware, error handlers
│   │   │   ├── models.py     # SQLAlchemy ORM models
│   │   │   ├── schemas.py    # Pydantic request/response schemas
│   │   │   ├── security.py   # JWT & password utilities
│   │   │   ├── db.py         # Database connection & pooling
│   │   │   ├── config.py     # Settings management
│   │   │   ├── routers/      # API endpoints (auth, invoices, clients, payments)
│   │   │   ├── services/     # Business logic (PDF generation)
│   │   │   └── scripts/      # Utility scripts (seeding)
│   │   ├── migrations/       # Alembic database migrations
│   │   ├── tests/            # Pytest test suite
│   │   └── pyproject.toml    # Python dependencies (uv)
│   └── frontend/             # Nuxt 3 application
│       ├── pages/            # Route components (dashboard, invoices, clients)
│       ├── components/       # Reusable UI components
│       ├── stores/           # Pinia state stores
│       ├── composables/      # Vue composables (API client)
│       ├── middleware/       # Route guards (auth)
│       └── layouts/          # Page layouts
├── infra/
│   ├── docker-compose.yml           # Development environment
│   ├── docker-compose.staging.yml   # Staging environment
│   ├── docker-compose.prod.yml      # Production environment
│   └── nginx/nginx.conf             # Reverse proxy config
└── scripts/
    └── run-checks.py         # Quality checks runner
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- For local development: Node.js 20+, Python 3.12+, PostgreSQL 16+

### Run the Application

```bash
# 1. Clone and navigate
gh repo clone viljoencor/invoice-tracker
cd invoice-tracker

# 2. Start all services (database, backend, frontend)
cd infra
docker compose up --build -d

# 3. Run database migrations
docker compose exec backend alembic upgrade head

# 4. Seed demo data (optional)
docker compose exec backend python -m app.scripts.seed

# 5. Access the application
# Frontend:  http://localhost:3000
# API Docs:  http://localhost:8000/docs
# Health:    http://localhost:8000/healthz
```

**Default Credentials**: `admin@example.com` / `admin123`

### Development Workflow

```bash
# Backend development
cd apps/backend
uv sync                    # Install dependencies
uv run pytest              # Run tests
uv run pytest --cov        # Run tests with coverage
uv run uvicorn app.main:app --reload  # Dev server

# Frontend development
cd apps/frontend
npm install
npm run dev

# Docker operations
cd infra
docker compose logs -f              # View logs
docker compose down                 # Stop services
docker compose down -v              # Stop and remove data
docker compose exec backend bash    # Shell into backend

# Database operations
docker compose exec backend alembic upgrade head                    # Apply migrations
docker compose exec backend alembic revision --autogenerate -m "msg"  # Create migration

# Quality checks
python scripts/run-checks.py       # Run all checks (lint, format, type, security, tests)
```

## Configuration

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment mode | `development` |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `JWT_SECRET` | JWT signing secret (32+ chars) | Required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `60` |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | Refresh token lifetime | `1440` |
| `DB_POOL_SIZE` | Connection pool size | `20` |
| `DB_MAX_OVERFLOW` | Max overflow connections | `10` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |
| `RATE_LIMIT_PER_MINUTE` | Requests per minute limit | `60` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `LOG_JSON_FORMAT` | JSON structured logging | `false` |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NUXT_PUBLIC_API_BASE` | Backend API URL | `http://localhost:8000` |
| `NODE_ENV` | Node environment | `development` |

## Deployment

### Development
```bash
cd infra
docker compose up --build
```

### Staging
```bash
cd infra
cp .env.staging.example .env
# Edit .env with staging values
docker compose -f docker-compose.staging.yml up -d
```

### Production
```bash
cd infra
cp .env.prod.example .env
# Edit .env with production values (strong JWT_SECRET, secure DATABASE_URL)
docker compose -f docker-compose.prod.yml up -d
```

**Production Checklist**:
- Generate strong JWT_SECRET (32+ characters)
- Use secure DATABASE_URL with strong credentials
- Enable LOG_JSON_FORMAT for structured logging
- Configure Nginx SSL certificates
- Set up database backups
- Configure monitoring and alerting

## Testing & Quality

```bash
# Run full test suite
cd apps/backend
uv run pytest --cov=app --cov-report=html

# Run quality checks
python scripts/run-checks.py

# Individual checks
cd apps/backend
uv run ruff check .          # Linting
uv run ruff format --check   # Format checking
uv run mypy app              # Type checking
uv run bandit -r app         # Security scanning
```

**Test Coverage**: >80% across unit, integration, and E2E tests

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login (returns JWT tokens)
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user

### Clients
- `GET /api/v1/clients` - List clients
- `POST /api/v1/clients` - Create client
- `GET /api/v1/clients/{id}` - Get client details
- `PUT /api/v1/clients/{id}` - Update client
- `DELETE /api/v1/clients/{id}` - Delete client

### Invoices
- `GET /api/v1/invoices` - List invoices (with filters)
- `POST /api/v1/invoices` - Create invoice
- `GET /api/v1/invoices/{id}` - Get invoice details
- `PUT /api/v1/invoices/{id}` - Update invoice
- `DELETE /api/v1/invoices/{id}` - Delete invoice
- `GET /api/v1/invoices/{id}/pdf` - Download invoice PDF

### Payments
- `GET /api/v1/payments` - List payments
- `POST /api/v1/payments` - Record payment
- `GET /api/v1/payments/{id}` - Get payment details
- `DELETE /api/v1/payments/{id}` - Delete payment

### Dashboard
- `GET /api/v1/dashboard/kpis` - Get key metrics
- `GET /api/v1/dashboard/revenue-chart` - Revenue trends

## Notes

- All monetary amounts stored as integer cents (avoid floating-point errors)
- All database queries are organization-scoped for multi-tenant isolation
- Frontend is SPA (SSR disabled) for simplified deployment
- PDF generation happens server-side using ReportLab
- Database migrations managed with Alembic
- Health checks available at `/healthz` (liveness) and `/readiness` (database)
