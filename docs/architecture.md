# Arquitectura

## Servicios

| Servicio | Responsabilidad | Estado |
|---|---|---|
| `auth` | Registro, login, OTP por correo, reset de contraseña, Google OAuth, emisión de JWT | Sin estado de negocio |
| `backend` | Cursos, progreso, exámenes, certificados, admin, media tokens | Dueño del schema `public` |
| `frontend` | SPA de estudiantes y panel admin | Estático (Vercel) |
| `landing` | Sitio público | Estático |
| R2 + Worker | Almacenamiento y streaming de media con token corto | Cloudflare |

## Decisiones

- **Auth como servicio aparte.** `apps/auth` es el único que conoce contraseñas, sesiones y proveedores. El backend solo confía en JWT firmados (EdDSA) verificados contra el JWKS del servicio.
- **Un Postgres, dos schemas.** `auth` (Better Auth) y `public` (Alembic). Un solo recurso en Railway, aislamiento lógico, y migraciones independientes. Si algún día el auth debe escalar o aislarse, se mueve el schema sin tocar el backend.
- **Rol y tenant en la DB, no en el JWT.** El JWT solo identifica (`sub`, `email`). `users.role` se lee de la DB en cada request (`require_role`).
- **JWT corto (15 min).** El frontend lo pide a `GET /api/auth/token` usando la cookie de sesión de Better Auth y lo renueva al expirar.

## Flujo de registro

1. `POST auth/api/auth/sign-up/email` → Better Auth crea el usuario (sin verificar) y envía OTP.
2. `POST auth/api/auth/email-otp/verify-email` → verifica y abre sesión (cookie).
3. `GET auth/api/auth/token` → JWT.
4. `POST backend/api/v1/auth/sync` con `Authorization: Bearer <JWT>` y `birth_date` → crea la fila en `users` (rol `estudiante`, forzado en servidor).

## Flujo de request autenticada

`Bearer JWT` → `verify_access_token` (JWKS cacheado 1 h; firma, `exp`, `iss`, `aud`) → `users` por `auth_user_id` → `require_role`. Si el usuario no existe: 409 `setup_required` (el frontend llama `/auth/sync`).
