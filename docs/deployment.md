# Despliegue

| Pieza | Plataforma |
|---|---|
| `frontend`, `landing` | Vercel (o su Dockerfile con nginx) |
| `auth`, `backend` | Railway (Dockerfile; cada uno con `railway.json`) |
| PostgreSQL | Railway (plugin Postgres) |
| Media | Cloudflare R2 + Worker (`infra/worker`) |
| Correo | Resend |

## Railway (proyecto único)
1. **Postgres**: añade el plugin.
2. **auth**: servicio desde el repo, *Root Directory* `apps/auth`.
3. **backend**: servicio desde el repo, *Root Directory* `apps/backend`.
4. Variables (usa referencias `${{Postgres.…}}` de Railway):

   **auth**
   ```
   DATABASE_URL=postgresql://…           # URL privada del Postgres
   DB_SSL=disable                        # privada; "require" si usas la pública
   DB_SCHEMA=auth
   BETTER_AUTH_URL=https://auth.<dominio>
   BETTER_AUTH_SECRET=<openssl rand -base64 32>
   TRUSTED_ORIGINS=https://app.<dominio>
   COOKIE_DOMAIN=.<dominio>
   RESEND_API_KEY=… EMAIL_FROM=…
   ```
   **backend**
   ```
   DATABASE_URL=postgresql+asyncpg://…   # misma base, driver asyncpg
   DB_SSL=disable
   AUTH_BASE_URL=https://auth.<dominio>
   AUTH_JWKS_URL=http://auth.railway.internal:3001/api/auth/jwks
   FRONTEND_URL=https://app.<dominio>
   R2_*  MEDIA_JWT_SECRET  RESEND_API_KEY  CERTIFICATE_VERIFY_BASE_URL
   ```
   `ALLOW_MOCK_AUTH` **no** debe existir en producción.
5. Dominios: `auth.<dominio>` → servicio auth; `api.<dominio>` → backend. Healthcheck `/health` ya está en `railway.json`.

## Vercel (frontend)
Build env: `PUBLIC_API_URL=https://api.<dominio>`, `VITE_AUTH_URL=https://auth.<dominio>`. Dominio `app.<dominio>`.

## Google OAuth (opcional)
Redirect URI autorizada: `https://auth.<dominio>/api/auth/callback/google`.

## Checklist de salida
- [ ] Postgres Railway creado; backend y auth healthy.
- [ ] `https://auth.<dominio>/api/auth/jwks` devuelve claves.
- [ ] Registro → OTP llega por Resend → login → `/api/v1/auth/me` responde 200.
- [ ] `ALLOW_MOCK_AUTH` ausente; `BETTER_AUTH_SECRET` único para producción.
- [ ] CORS del backend restringido al dominio del frontend (hoy `allow_origins=["*"]`, ver `app/main.py`).
- [ ] CORS del bucket R2 y del Worker incluyen el dominio nuevo.
