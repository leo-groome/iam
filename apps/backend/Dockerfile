FROM python:3.12-slim AS base
WORKDIR /app

RUN pip install uv

FROM base AS deps
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN adduser --disabled-password --gecos "" appuser
COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
