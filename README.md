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
- `DATABASE_URL`: PostgreSQL connection URL
- `JWT_SECRET`: Secret key for JWT tokens
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT access token expiry (default: 60)
- `REFRESH_TOKEN_EXPIRE_MINUTES`: JWT refresh token expiry (default: 1440)

Frontend:
- `NUXT_PUBLIC_API_BASE`: Backend API URL (default: http://localhost:8000)
- `NODE_ENV`: Node environment (development/production) (Nuxt 3 + FastAPI + PostgreSQL)

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

## Scripts of interest
- `alembic upgrade head` – applies migrations
- `python -m app.scripts.seed` – seeds org/user/clients/invoice

## Notes
- Money stored in integer cents
- Queries are org-scoped (multi-tenant-ready, simple filter)
- PDF endpoint returns a generated PDF from server-side (pure Python)