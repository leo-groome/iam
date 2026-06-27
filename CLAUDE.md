# IAM — Plataforma de Cursos (Infancia y Adolescencia Misionera)

## Stack
- **Frontend:** Vue 3 SPA + Vue Router + Pinia + Tailwind (Vite) — deploy en Vercel
- **Backend:** FastAPI (Python 3.12) + SQLAlchemy 2.0 async + asyncpg — deploy en Railway
- **DB:** PostgreSQL en Neon.com (`postgresql+asyncpg://`)
- **Auth:** Neon Auth — JWT validado en `/api/v1/auth/me`, expuesto via Pinia `useAuthStore()`
- **Storage:** Cloudflare R2 (media/certificados)
- **Email:** Resend

## Monorepo
```
apps/
  backend/   FastAPI app
  frontend/  Vue 3 SPA
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
1. Frontend obtiene JWT vía Neon Auth (lib `@stackframe/js`)
2. `apiFetch` en `src/lib/api.ts` añade `Authorization: Bearer <token>` a cada request
3. `useAuthStore` (Pinia) mantiene `user` reactivo cargado desde `/api/v1/auth/me`
4. Router guard en `src/router/index.ts` redirige a `/login` si `requiresAuth` y no hay sesión
5. Rutas privadas: `/catalogo`, `/curso/:slug/*`, `/perfil`, `/admin/*`

## Frontend — convenciones de servicios
- `src/services/courses.service.ts` — endpoints **públicos** (estudiantes): `GET /api/v1/courses`, `/api/v1/courses/:slug`, exámenes de tema
- `src/services/admin.service.ts` — endpoints **admin/instructor**: cursos, módulos, temas, preguntas, opciones, estudiantes, reportes
- Todos los paths llevan prefijo completo `/api/v1/...`
- IDs de rutas admin son **UUIDs** (`:id`, `:modId`, `:temaId`, `:qId`); rutas de estudiante usan **slug** (`:slug`, `:topicId`)

## Admin panel
- `/admin/cursos/:id` → editar curso (sin restricción de edad)
- `/admin/cursos/:id/modulos/:modId` → editar módulo: descripción + lista de Clases (temas) + sección "Examen Diagnóstico del Módulo"
- `/admin/cursos/:id/modulos/:modId/temas/:temaId` → editar tema: content_type (video/pdf/imagen/texto), duración, has_exam, exam_min_score, content_body
- `/admin/cursos/:id/modulos/:modId/temas/:temaId/preguntas/:qId` → editar pregunta de tema (3-5 opciones, exactamente 1 correcta)
- `/admin/cursos/:id/modulos/:modId/examen-diagnostico/:qId` → editar pregunta diagnóstica a nivel módulo (reusa `AdminPreguntaDetalle.vue`)

## DB — convenciones
- SSL inyectado via `connect_args={"ssl": "require"}` en el engine (no en la URL)
- URL limpia: `postgresql+asyncpg://...host/neondb` (sin query params)
- UUIDs como PK en todas las tablas
- Timestamps con timezone en todos los modelos (`TimestampMixin`)
- Migraciones en `apps/backend/alembic/versions/`

## Modelos principales
`User` · `Course` · `Module` · `Topic` · `Question` · `Option` · `Enrollment` · `TopicProgress` · `ExamAttempt` · `Certificate` · `AdminAudit`

### Notas sobre el dominio
- **Sin restricción por edad:** `Course.age_min`/`age_max` aún existen en DB pero ya no se filtran ni se exponen en UI. Todos los cursos publicados son visibles a todos los usuarios.
- **`Question` XOR:** una pregunta pertenece a `topic_id` (examen de clase) o `module_id` (examen diagnóstico del módulo), nunca a ambos.
- **Validaciones:** preguntas requieren 3-5 opciones, exactamente 1 marcada `is_correct=true`. Topics con progress no se pueden borrar (HTTP 409).

## Endpoints admin clave
```
GET    /api/v1/admin/topics/{id}                    → topic + preguntas + opciones
GET    /api/v1/admin/questions/{id}                 → pregunta con opciones
GET    /api/v1/admin/modules/{id}/questions         → preguntas del examen diagnóstico
POST   /api/v1/admin/modules/{id}/questions         → crear pregunta diagnóstica
POST   /api/v1/admin/topics/{id}/questions          → crear pregunta de clase
PATCH  /api/v1/admin/questions/{id}                 → editar enunciado (NO afecta intentos históricos)
DELETE /api/v1/admin/questions/{id}                 → soft-delete (`archived_at`)
PATCH  /api/v1/admin/options/{id}                   → editar texto/correctitud
```

## Media & Storage (R2)
- **Subida directa:** El administrador sube archivos directamente a R2 desde el navegador usando URLs firmadas por el backend (`POST /api/v1/media/upload-url`). 
- **CORS del Bucket:** El bucket de R2 debe tener configurada una política de CORS para permitir métodos `PUT` y `OPTIONS` desde `http://localhost:4321` y dominios de producción.
- **URLs de Portada (Covers):** Las portadas son públicas, servidas por el worker de R2 bajo el prefijo `cover/` con `Access-Control-Allow-Origin: *` y `Cross-Origin-Resource-Policy: cross-origin` para permitir embebido seguro bajo COEP.
- **Reproductor del Estudiante (`LearningPlayer.vue`):**
  - Carga el tema detallado usando `GET /api/v1/topics/{topic_id}` en `LessonView.vue` para obtener de forma segura el `media_key` (el catálogo `/courses/{slug}` oculta `media_key` por privacidad).
  - Los **videos** se reproducen usando streaming directo con soporte de HTTP Range Requests (`206 Partial Content`) pasando el token en la consulta (`?token=...`) y con `crossorigin="anonymous"` en la etiqueta `<video>`.
  - Los **PDFs e imágenes** privados se descargan como blob en memoria (`URL.createObjectURL(blob)`).
  - El worker de R2 inyecta `Cross-Origin-Resource-Policy: cross-origin` y `Access-Control-Allow-Origin` dinámico para evitar bloqueos por políticas COEP estrictas (`require-corp`) del servidor de desarrollo del frontend.


