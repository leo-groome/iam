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
  security/        JWT validation (Neon Auth)
alembic/           Migraciones
```

## DB
- Driver: `asyncpg` — URL sin query params, SSL via `connect_args={"ssl": "require"}`
- Pool: `size=5`, `max_overflow=10`, `pre_ping=True`, `recycle=300`
- Base declarativa: `app/models/base.py` — `Base`, `TimestampMixin`, `new_uuid()`

## Auth
- Neon Auth JWKS — validación en `app/security/neon_auth.py`
- `get_current_user` dep en `app/deps.py` → retorna `User` ORM
- Mock auth disponible con `ALLOW_MOCK_AUTH=true` (solo dev)

## Tests
```bash
uv run pytest
```
