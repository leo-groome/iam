# Desarrollo

## Todo en Docker (recomendado)
```bash
docker compose up --build          # db + auth + backend + frontend + s3 mock + media gateway
docker compose logs -f auth        # OTP de registro en dev (sin RESEND_API_KEY)
docker compose down -v             # borra también los volúmenes
```
Usuarios mock para QA/E2E:
```bash
ALLOW_MOCK_AUTH=true docker compose up -d --build
docker compose --profile seed run --rm seed
```

## Servicio por servicio
Levanta solo la DB: `docker compose up -d db` (Postgres en `localhost:5433`, user/pass/db = `iam`).

```bash
# auth
cd apps/auth && cp .env.example .env && pnpm install
pnpm migrate:dev && pnpm dev            # :3001

# backend
cd apps/backend && cp .env.example .env && uv sync
set -a && source .env && set +a && uv run alembic upgrade head
uv run uvicorn app.main:app --reload    # :8000

# frontend
cd apps/frontend && cp .env.example .env && pnpm install && pnpm dev   # :4321
```
Ajusta `.env` locales: `DATABASE_URL` a `localhost:5433` con `DB_SSL=disable`, `AUTH_BASE_URL=http://localhost:3001`.

## Tests
```bash
cd apps/backend && uv run pytest                                   # SQLite, sin dependencias
cd apps/auth && TEST_DATABASE_URL=postgresql://iam:iam@localhost:5433/iam pnpm test
cd apps/frontend && pnpm build                                     # gate de CI
```

## Vue DevTools
El overlay está apagado por defecto (tapaba botones en QA). Actívalo con `VITE_DEVTOOLS=true pnpm dev`.

## Estado conocido
- `ruff check` en el backend tiene deuda previa (informativo en CI).
- `vue-tsc` en el frontend tiene errores de tipos previos; el gate es `pnpm build`.
