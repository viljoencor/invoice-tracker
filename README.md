# Invoice Tracker

A production-ready full-stack invoice management system with multi-tenant architecture, designed for small businesses to track invoices, clients, and payments.

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
