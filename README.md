# IAM — Plataforma de Cursos

[![CI](https://github.com/leo-groome/iam/actions/workflows/ci.yml/badge.svg)](https://github.com/leo-groome/iam/actions/workflows/ci.yml)

Campus en línea de **Infancia y Adolescencia Misionera**: cursos con contenido por bloques (video, PDF, imagen, audio, texto), exámenes, progreso, certificados y panel de administración.

## Arquitectura

```
                 ┌───────────────┐   cookie de sesión    ┌──────────────────┐
  Navegador ───▶ │  frontend     │ ───────────────────▶  │  auth            │
                 │  Vue 3 SPA    │   JWT (15 min, EdDSA) │  Better Auth     │
                 └──────┬────────┘ ◀───────────────────  └────────┬─────────┘
                        │ Authorization: Bearer <JWT>             │ schema `auth`
                        ▼                                         ▼
                 ┌───────────────┐   valida firma vía JWKS  ┌──────────────────┐
                 │  backend      │ ◀─────────────────────── │  PostgreSQL      │
                 │  FastAPI      │ ───── schema `public` ─▶ │  (Railway)       │
                 └──────┬────────┘                          └──────────────────┘
                        ▼
                 Cloudflare R2 (media) · Resend (correo)
```

| Servicio | Ruta | Stack | Puerto dev |
|---|---|---|---|
| Frontend | `apps/frontend` | Vue 3 + Pinia + Tailwind (Vite) | 4321 |
| Landing | `apps/landing` | Astro | — |
| Auth | `apps/auth` | Better Auth + Hono (Node 22) | 3001 |
| Backend | `apps/backend` | FastAPI + SQLAlchemy 2 async | 8000 |
| DB | — | PostgreSQL 17 (Railway en prod) | 5433 |

Una sola base PostgreSQL con **dos schemas**: `public` (app, migraciones Alembic) y `auth` (Better Auth, migraciones de su CLI). El backend nunca lee tablas de `auth`; solo valida el JWT y mapea `sub` → `users.auth_user_id`.

## Arranque rápido

Requisitos: Docker + Docker Compose.

```bash
docker compose up --build
```

- Frontend: <http://localhost:4321> · Auth: <http://localhost:3001/health> · API: <http://localhost:8000/docs>
- Sin `RESEND_API_KEY`, los códigos OTP de registro se imprimen en los logs de `auth` (solo dev): `docker compose logs -f auth`.
- Usuarios mock para QA/E2E: `ALLOW_MOCK_AUTH=true docker compose --profile seed run --rm seed`.

Desarrollo sin Docker, tests y migraciones: [docs/development.md](docs/development.md).

## Estructura

```
apps/
  auth/        Better Auth (servicio propio, su Dockerfile y migraciones)
  backend/     FastAPI
  frontend/    Vue 3 SPA
  landing/     Astro
infra/
  worker/      Cloudflare Worker (stream de media desde R2)
  local-media/ Gateway S3 local para desarrollo
docs/          Documentación (ver índice)
.github/workflows/ci.yml
compose.yaml   Entorno de desarrollo completo
```

## Documentación

Índice completo en [docs/README.md](docs/README.md).

| Doc | Contenido |
|---|---|
| [architecture.md](docs/architecture.md) | Servicios, flujos, decisiones |
| [development.md](docs/development.md) | Setup local, comandos, tests |
| [auth.md](docs/auth.md) | Better Auth: configuración, flujo JWT, endpoints |
| [database.md](docs/database.md) | Schemas, migraciones, Railway |
| [deployment.md](docs/deployment.md) | Railway + Vercel, variables, checklist |
| [ci.md](docs/ci.md) | Pipeline de GitHub Actions |
