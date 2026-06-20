# IAM — Plataforma de Cursos (Infancia y Adolescencia Misionera)

## Stack
- **Frontend:** Astro (SSR) + Vue 3 + Tailwind — deploy en Vercel
- **Backend:** FastAPI (Python 3.12) + SQLAlchemy 2.0 async + asyncpg — deploy en Railway
- **DB:** PostgreSQL en Neon.com (`postgresql+asyncpg://`)
- **Auth:** Neon Auth — JWT validado en `/api/v1/auth/me`, propagado como `Astro.locals.user`
- **Storage:** Cloudflare R2 (media/certificados)
- **Email:** Resend

## Monorepo
```
apps/
  backend/   FastAPI app
  frontend/  Astro + Vue app
```

## Dev
```bash
# Backend (desde apps/backend/)
uv run uvicorn app.main:app --reload

# Frontend (desde apps/frontend/)
pnpm dev

# Migraciones
cd apps/backend && set -a && source .env && set +a && uv run alembic upgrade head
```

## Auth flow
1. Frontend recibe JWT de Neon Auth → guarda en cookie `neon-auth-token`
2. Middleware Astro (`src/middleware.ts`) llama `/api/v1/auth/me` en cada request SSR
3. Usuario disponible en todas las páginas como `Astro.locals.user` (`{ id, email, fullName, role, status }`)
4. Rutas privadas: `/catalogo`, `/curso/*`, `/perfil`, `/admin/*`

## DB — convenciones
- SSL inyectado via `connect_args={"ssl": "require"}` en el engine (no en la URL)
- URL limpia: `postgresql+asyncpg://...host/neondb` (sin query params)
- UUIDs como PK en todas las tablas
- Timestamps con timezone en todos los modelos (`TimestampMixin`)
- Migraciones en `apps/backend/alembic/versions/`

## Modelos principales
`User` · `Course` · `Module` · `Topic` · `Question` · `Option` · `Enrollment` · `TopicProgress` · `ExamAttempt` · `Certificate` · `AdminAudit`
