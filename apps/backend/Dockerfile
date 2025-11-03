# apps/backend/Dockerfile

# 1) Build deps into .venv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS deps
WORKDIR /app
COPY pyproject.toml README.md ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

# 2) Build stage (copy code + .venv)
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS build
WORKDIR /app
COPY --from=deps /app/.venv ./.venv
COPY alembic.ini ./
COPY migrations migrations/
COPY app app/
RUN touch README.md
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# 3) Runtime (keep Python from uv base so .venv works)
FROM ghcr.io/astral-sh/uv:python3.12-bookworm
WORKDIR /app
COPY --from=build /app/.venv ./.venv
COPY --from=build /app/alembic.ini ./
COPY --from=build /app/migrations migrations/
COPY --from=build /app/app app/
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
WORKDIR /app
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]
