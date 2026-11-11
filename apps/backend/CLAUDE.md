# Backend — FastAPI

## Setup
```bash
# Instalar deps
uv sync

# Variables de entorno
cp .env.example .env  # rellenar valores reales

# Correr servidor
uv run uvicorn app.main:app --reload

# Migraciones
set -a && source .env && set +a
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "descripcion"
```

## Estructura
```
app/
  main.py          FastAPI app + routers
  config.py        Settings (pydantic-settings, carga .env)
  db.py            Engine async + AsyncSessionLocal + get_db()
  deps.py          Dependencias FastAPI (get_current_user, etc.)
  models/          SQLAlchemy ORM models
  routers/         Endpoints por dominio (auth, courses, admin…)
  security/        JWT validation (Better Auth, JWKS)
alembic/           Migraciones
```

## DB
- Driver: `asyncpg` — URL sin query params, SSL via `DB_SSL` + `connect_args`
- Pool: `size=5`, `max_overflow=10`, `pre_ping=True`, `recycle=300`
- Base declarativa: `app/models/base.py` — `Base`, `TimestampMixin`, `new_uuid()`

## Auth
- Better Auth JWKS — validación en `app/security/auth_jwt.py` (`AUTH_BASE_URL`, `AUTH_JWKS_URL`)
- `get_current_user` dep en `app/deps.py` → retorna `User` ORM
- Mock auth disponible con `ALLOW_MOCK_AUTH=true` (solo dev)

## Tests
```bash
uv run pytest
```
