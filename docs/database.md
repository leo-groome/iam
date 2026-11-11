# Base de datos

PostgreSQL 17 en **Railway**. Un solo servidor, dos schemas:

| Schema | Dueño | Migraciones |
|---|---|---|
| `public` | backend (SQLAlchemy) | Alembic: `apps/backend/alembic/versions/` |
| `auth` | Better Auth | `apps/auth` (`node dist/migrate.js`) |

Alembic solo ve `public` (no usa `include_schemas`), así que nunca toca `auth`.

## Convenciones
UUID como PK; `TIMESTAMPTZ`; dinero en `Numeric`; nunca `create_all` en producción. `users.auth_user_id` = `user.id` de Better Auth (migración `i7e8f9a0b1c2` renombró `neon_user_id`).

## Migraciones (backend)
```bash
cd apps/backend
set -a && source .env && set +a
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "descripcion"
```
El contenedor del backend ejecuta `alembic upgrade head` al arrancar. CI valida `upgrade → downgrade -1 → upgrade` sobre Postgres real.

## Conexión en Railway
- Entre servicios de Railway: URL **privada** (`postgres.railway.internal`), `DB_SSL=disable`.
- Desde tu máquina: URL pública (TCP proxy), `DB_SSL=require`.
- El backend usa `postgresql+asyncpg://…`; auth usa `postgresql://…` (misma base).

## Migración Neon → Railway
Se decidió arrancar **vacío** (solo había datos de prueba): crear el Postgres en Railway, desplegar `backend` (corre Alembic) y `auth` (crea `auth`) y listo. Si en el futuro hay que mover datos reales:
```bash
pg_dump --no-owner --no-acl -Fc "$OLD_URL" -f iam.dump
pg_restore --no-owner --no-acl --clean --if-exists -d "$NEW_URL" iam.dump
```
Los usuarios de Neon Auth **no** se migran con esto (hashes y sesiones viven en otro sistema).
