# Invoice Tracker

A full-stack invoice management application built with FastAPI, Nuxt 3, and PostgreSQL.

## Project Structure

```
/
├── apps/
│   ├── backend/         # FastAPI backend
│   └── frontend/        # Nuxt 3 frontend
└── infra/              # Docker and infrastructure files
```

## Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local development)
- Python 3.12+ (for local development)
- PostgreSQL 16+ (for local development)

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd invoice-tracker
   ```

2. Start the development environment:
   ```bash
   cd infra
   docker compose up -d
   ```

3. Run database migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. Seed the database:
   ```bash
   docker compose exec backend python -m app.scripts.seed
   ```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Default login: admin@example.com / admin123

## Development Commands

### Backend

```bash
# Build backend
cd infra
docker compose build backend

# Start backend
docker compose up -d backend

# Run migrations
docker compose exec backend alembic upgrade head

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "latest"

# Run seed script
docker compose exec backend python -m app.scripts.seed

# View logs
docker compose logs -f backend
```

### Frontend

```bash
# Build frontend NOTE(TAKES 15-MIN TO BUILD)
cd infra
docker compose build frontend

# Start frontend
docker compose up -d frontend

# View logs
docker compose logs -f frontend
```
### Common Tasks

```bash
# Rebuild and restart all services
cd infra
docker compose down
docker compose build
docker compose up -d

# Stop all services
docker compose down

# Stop and remove all data (including database)
docker compose down -v

# View all logs
docker compose logs -f
```

## Configuration

### Environment Variables

Backend:
- `ENVIRONMENT`: Application environment (development/staging/production)
- `DATABASE_URL`: PostgreSQL connection URL
- `JWT_SECRET`: Secret key for JWT tokens (minimum 32 characters)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT access token expiry (default: 60)
- `REFRESH_TOKEN_EXPIRE_MINUTES`: JWT refresh token expiry (default: 1440)
- `DB_POOL_SIZE`: Database connection pool size (default: 20)
- `DB_MAX_OVERFLOW`: Max overflow connections (default: 10)
- `DB_POOL_RECYCLE`: Connection recycle time in seconds (default: 3600)
- `RATE_LIMIT_ENABLED`: Enable rate limiting (default: true)
- `RATE_LIMIT_PER_MINUTE`: Rate limit per minute (default: 60)
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_JSON_FORMAT`: Use JSON logging format (default: false)

Frontend:
- `NUXT_PUBLIC_API_BASE`: Backend API URL (default: http://localhost:8000)
- `NODE_ENV`: Node environment (development/production)

Lean, production-minded MVP you can run locally with Docker Compose.

## Quickstart

```bash
# 1) Copy env and adjust secrets if needed
cp .env.example .env

# 2) Build & run (frontend, backend, db)
docker compose -f infra/docker-compose.yml up --build

# 3) Apply DB migrations (one-time in another terminal)
docker compose -f infra/docker-compose.yml exec backend alembic upgrade head

# 4) Seed a demo org, user, and sample data (optional)
docker compose -f infra/docker-compose.yml exec backend python -m app.scripts.seed
```

# Frontend → http://localhost:3000
# API docs → http://localhost:8000/docs
# Health   → http://localhost:8000/healthz

Default credentials (after seeding):
Email: admin@example.com
Password: admin123

## Stack

Frontend: Nuxt 3, Pinia, Tailwind

Backend: FastAPI (async), SQLAlchemy 2.0 (async), Pydantic v2, Alembic

Auth: JWT (HS256), Argon2 password hashing

DB: PostgreSQL 16

PDF: ReportLab with a thin adapter (easy to swap later)

## Production-Ready Features

The application includes comprehensive production-ready enhancements:

### Security & Authentication
- ✅ **JWT Secret Validation**: Enforces strong secrets (32+ chars) in production
- ✅ **Rate Limiting**: Prevents brute force attacks on auth endpoints (60 req/min default)
- ✅ **Security Scanning**: Automated vulnerability scanning with Bandit and Trivy

### Database & Performance
- ✅ **Database Connection Pooling**: Explicit pool configuration (20 connections, 10 overflow)
- ✅ **Connection Retry Logic**: Automatic retry with exponential backoff on startup
- ✅ **Health Checks**: `/healthz` (liveness) and `/readiness` (database connectivity)

### Observability & Monitoring
- ✅ **Structured Logging**: JSON logging for production, pretty logs for development
- ✅ **Global Exception Handling**: Catches unhandled exceptions, sanitized errors in production
- ✅ **Environment Detection**: Different behavior for development/staging/production

### Testing & Quality
- ✅ **Comprehensive Test Suite**: Unit, integration, and E2E tests with >80% coverage
- ✅ **Automated Linting**: Ruff for code style and quality checks
- ✅ **Type Checking**: MyPy for static type analysis
- ✅ **CI/CD Pipeline**: Automated testing, security scanning, and deployment

### Deployment
- ✅ **Multi-Environment Support**: Separate configs for dev/staging/production
- ✅ **Docker Health Checks**: All services include health check configuration
- ✅ **Nginx Reverse Proxy**: Production-ready reverse proxy with SSL and rate limiting
- ✅ **Rolling Updates**: Zero-downtime deployment support

## Documentation

- 📘 [Production Setup Guide](PRODUCTION-SETUP.md) - Security, logging, monitoring, and production deployment
- 📘 [Testing & CI/CD Guide](TESTING.md) - Testing strategy, CI/CD pipeline, and quality gates
- 📘 [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## Development Commands

Use the Makefile for common tasks:

```bash
# Show all available commands
make help

# Development workflow
make dev              # Start everything (build, migrate, seed)
make test             # Run tests with coverage
make quality          # Run all quality checks (lint, format, type-check, security)

# Docker operations
make docker-up        # Start all services
make docker-down      # Stop all services
make docker-logs      # View logs

# Database operations
make migrate          # Run migrations
make seed            # Seed test data
make migrate-create msg="description"  # Create new migration

# Code quality
make lint            # Check linting
make format          # Format code
make type-check      # Run type checking
make security-check  # Security scan
```

## Testing

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run with verbose output
make test-verbose

# Run specific test file
cd apps/backend && uv run pytest tests/test_auth.py
```

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

## Deployment

### Development
```bash
make dev  # Starts everything with migrations and seed data
```

### Staging
```bash
cd infra
cp .env.staging.example .env
# Edit .env with your values
docker compose -f docker-compose.staging.yml up -d
```

### Production
```bash
cd infra
cp .env.prod.example .env
# Edit .env with production values
docker compose -f docker-compose.prod.yml up -d
```

See [PRODUCTION-SETUP.md](PRODUCTION-SETUP.md) for detailed deployment guide.

## Notes
- Money stored in integer cents
- Queries are org-scoped (multi-tenant-ready, simple filter)
- PDF endpoint returns a generated PDF from server-side (pure Python)
- Health checks configured for all services
- Comprehensive test coverage (unit, integration, E2E)