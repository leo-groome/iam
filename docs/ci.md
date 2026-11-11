# CI (GitHub Actions)

Workflow: `.github/workflows/ci.yml`. Corre en cada PR y en push a `main`.

| Job | Qué valida |
|---|---|
| `backend` | `pytest`; migraciones Alembic `upgrade → downgrade -1 → upgrade` sobre Postgres 17; `ruff` (informativo) |
| `auth` | `tsc --noEmit`, build, tests de integración contra Postgres (JWKS EdDSA, rechazo de credenciales, CORS) |
| `frontend` | `pnpm build` |
| `landing` | `pnpm build` |
| `docker` | Construye las 4 imágenes (sin push) tras pasar lo anterior |
| `compose` | `docker compose config -q` |

Versiones fijadas: Node 22, pnpm 10.11.0, Postgres 17, uv desde `uv.lock` (`--frozen`).

## Pendiente
- Volver bloqueante `ruff` y `vue-tsc` cuando se salde la deuda.
- Tests E2E (Playwright) en CI.
- Despliegue: hoy lo hace la integración nativa de Railway/Vercel desde GitHub; para exigir CI verde antes de desplegar, activa *Wait for CI* en Railway y branch protection en `main`.
