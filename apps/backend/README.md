# Invoice Tracker Backend

FastAPI backend for Invoice Tracker application. Handles invoices, clients, payments, and PDF generation.

## Quick Start

### Install Dependencies
```bash
uv sync
```

### Run Tests
```bash
uv run pytest
```

Or with coverage:
```bash
uv run pytest --cov=app --cov-report=html
```

### Run Server
```bash
uv run uvicorn app.main:app --reload
```