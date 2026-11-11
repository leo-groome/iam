# Auth (Better Auth)

Servicio en `apps/auth` (Hono + [Better Auth](https://www.better-auth.com)). Código: `src/auth.ts` (config), `src/app.ts` (HTTP), `src/migrate.ts` (migraciones), `src/email.ts` (Resend).

## Capacidades
Email + contraseña (verificación obligatoria por OTP de 6 dígitos, 10 min, 3 intentos), reset de contraseña por OTP, Google OAuth (opcional), rate limit en DB, plugin `jwt` (EdDSA/Ed25519, 15 min).

## Endpoints (prefijo `/api/auth`)
| Endpoint | Uso |
|---|---|
| `POST /sign-up/email`, `POST /sign-in/email`, `POST /sign-out` | Cuenta y sesión (cookie) |
| `POST /email-otp/verify-email` · `send-verification-otp` | Verificación de correo |
| `POST /email-otp/request-password-reset` · `reset-password` | Recuperar contraseña |
| `GET /token` | JWT para el backend (requiere cookie de sesión) |
| `GET /jwks` | Claves públicas (las consume el backend) |
| `GET /health` (raíz, sin prefijo) | Healthcheck (Railway) |

## Variables (`apps/auth/.env.example`)
| Variable | Notas |
|---|---|
| `BETTER_AUTH_URL` | URL pública del servicio. Es `iss` y `aud` del JWT |
| `BETTER_AUTH_SECRET` | ≥32 chars. `openssl rand -base64 32`. Rotarlo invalida sesiones |
| `DATABASE_URL`, `DB_SSL`, `DB_SCHEMA` | Postgres (`DB_SCHEMA=auth`). `DB_SSL=disable` por red privada de Railway (recomendado); `require` verifica el certificado (`DB_CA_CERT` si el CA no es público); `no-verify` desactiva la verificación, evítalo |
| `TRUSTED_ORIGINS` | CSV de orígenes del frontend/landing (CORS + CSRF de Better Auth) |
| `COOKIE_DOMAIN` | Opcional (`.tudominio.com`) para compartir cookie entre subdominios |
| `RESEND_API_KEY`, `EMAIL_FROM` | Obligatorio en producción |
| `GOOGLE_CLIENT_ID/SECRET` | Opcional |

## Cookies entre dominios
Frontend y auth en **subdominios del mismo dominio** (`app.x.com` / `auth.x.com`) + `COOKIE_DOMAIN=.x.com`. Con dominios distintos (p. ej. `*.vercel.app` y `*.up.railway.app`) los navegadores bloquean la cookie de terceros y el login falla: usa dominio propio.

## Validación en el backend
`apps/backend/app/security/auth_jwt.py`: JWKS desde `AUTH_JWKS_URL` (por defecto `${AUTH_BASE_URL}/api/auth/jwks`), algoritmo fijo EdDSA, `iss`/`aud` = `AUTH_BASE_URL`, `exp`/`iat` obligatorios. En Railway apunta `AUTH_JWKS_URL` a la URL privada del servicio auth.

## Migraciones
`node dist/migrate.js` (lo ejecuta el contenedor antes de arrancar): crea el schema `auth` y aplica las tablas de Better Auth. Es idempotente. Al añadir plugins que cambian el esquema, vuelve a desplegar y se aplican solas.

## Usuarios mock (solo QA)
`ALLOW_MOCK_AUTH=true` en el backend acepta tokens `mock-token:<sub>:<email>:<nombre>:<rol>`. **Nunca en producción.**
