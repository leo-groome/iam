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
- `/admin/cursos/:id/modulos/:modId/temas/:temaId` → editar tema: has_exam, exam_min_score + **editor de bloques de contenido** (`AdminContentBlocks.vue`): lista ordenable de bloques de tipo video/pdf/imagen/audio/texto. Los bloques `texto` usan editor WYSIWYG Tiptap (`RichTextEditor.vue`). Se guardan vía `PUT /api/v1/admin/topics/{id}/blocks` (reemplazo total de la lista)
- `/admin/cursos/:id/modulos/:modId/temas/:temaId/preguntas/:qId` → editar pregunta de tema (3-5 opciones, exactamente 1 correcta)
- `/admin/cursos/:id/modulos/:modId/examen-diagnostico/:qId` → editar pregunta diagnóstica a nivel módulo (reusa `AdminPreguntaDetalle.vue`)

## DB — convenciones
- SSL inyectado via `connect_args={"ssl": "require"}` en el engine (no en la URL)
- URL limpia: `postgresql+asyncpg://...host/neondb` (sin query params)
- UUIDs como PK en todas las tablas
- Timestamps con timezone en todos los modelos (`TimestampMixin`)
- Migraciones en `apps/backend/alembic/versions/`

## Modelos principales
`User` · `Course` · `Module` · `Topic` · `ContentBlock` · `Question` · `Option` · `Enrollment` · `TopicProgress` · `ContentBlockProgress` · `ExamAttempt` · `Certificate` · `AdminAudit`

### Notas sobre el dominio
- **Sin restricción por edad:** `Course.age_min`/`age_max` aún existen en DB pero ya no se filtran ni se exponen en UI. Todos los cursos publicados son visibles a todos los usuarios.
- **Contenido por bloques:** una clase (`Topic`) tiene N `ContentBlock` ordenables (`order_index`), cada uno de tipo `video|pdf|imagen|audio|texto`. El estudiante los ve todos renderizados. Las columnas legacy `Topic.content_type`/`media_key`/`content_body`/`duration_seconds` se conservan (no se dropearon) para catálogo/listados; `content_type` se sincroniza con el kind del primer bloque en cada guardado. Un tema debe tener ≥1 bloque.
- **Progreso por bloque:** `ContentBlockProgress` (unique por `user_id`+`block_id`) rastrea el avance de cada bloque de media. `TopicProgress` sigue siendo la fuente de verdad del `state` de la clase (`bloqueado|disponible|contenido_visto|aprobado|en_repaso`).
- **Gating de completado:** solo los bloques **`video` y `pdf`** son requisito para completar una clase (video ≥95% + ≥5s; pdf `pdf_last_page ≥ pdf_total_pages` con conteo real de pdf.js). `audio/imagen/texto` son complementarios. Un tema sin bloques requeridos se completa por honor-system vía `mark-content-done`. La duración del video para el % viene de `block.duration_seconds` (auto-detectada, autoritativa), no del cliente.
- **Editar bloques resetea progreso:** `PUT /admin/topics/{id}/blocks` borra y recrea bloques (borra su `ContentBlockProgress` por cascade) y devuelve a `disponible` los `TopicProgress` no-`aprobado` del tema. Los `aprobado` (examen ya pasado) se respetan.
- **`Question` XOR:** una pregunta pertenece a `topic_id` (examen de clase) o `module_id` (examen diagnóstico del módulo), nunca a ambos.
- **Validaciones:** preguntas requieren 3-5 opciones, exactamente 1 marcada `is_correct=true`. Topics con progress no se pueden borrar (HTTP 409). `ContentBlock` de media exige `media_key` con el prefijo de scope correcto (`video/`, `pdf/`, …); los de `texto` exigen `content_body` y `media_key=null`.

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
PUT    /api/v1/admin/topics/{id}/blocks             → reemplaza la lista completa de ContentBlock del tema
```

## Endpoints estudiante clave (contenido)
```
GET    /api/v1/topics/{id}                           → tema + blocks[] (con progreso por bloque)
POST   /api/v1/media/play-token                      → { block_id } → token JWT corto para stream/descarga del bloque
POST   /api/v1/topics/{id}/heartbeat                 → { type, block_id, ... } progreso por bloque (video/audio: pos+pct; pdf: last_page/total_pages)
POST   /api/v1/topics/{id}/mark-content-done         → completa la clase (valida gating de video+pdf en server)
```

## Media & Storage (R2)
- **Subida directa:** El administrador sube archivos directamente a R2 desde el navegador usando URLs firmadas por el backend (`POST /api/v1/media/upload-url`). 
- **CORS del Bucket:** El bucket de R2 debe tener configurada una política de CORS para permitir métodos `PUT` y `OPTIONS` desde `http://localhost:4321` y dominios de producción.
- **URLs de Portada (Covers):** Las portadas son públicas, servidas por el worker de R2 bajo el prefijo `cover/` con `Access-Control-Allow-Origin: *` y `Cross-Origin-Resource-Policy: cross-origin` para permitir embebido seguro bajo COEP.
- **Reproductor del Estudiante (`LearningPlayer.vue` + `ContentBlockPlayer.vue`):**
  - `LessonView.vue` carga el tema con `GET /api/v1/topics/{topic_id}` (incluye `blocks[]`; el catálogo `/courses/{slug}` oculta `media_key` por privacidad). `LearningPlayer.vue` itera los bloques ordenados y renderiza cada uno con `ContentBlockPlayer.vue`.
  - Cada bloque de media pide su token con `POST /api/v1/media/play-token { block_id }`.
  - Los **videos/audio** se reproducen con streaming directo (HTTP Range `206`) pasando el token en la consulta (`?token=...`) y `crossorigin="anonymous"`.
  - Las **imágenes** privadas se descargan como blob (`URL.createObjectURL`).
  - Los **PDFs** se renderizan con **pdf.js** (`pdfjs-dist`): se descarga el blob (`mediaFetch`, Bearer), se renderiza cada página a `<canvas>` y un `IntersectionObserver` rastrea la última página vista para el gating real (heartbeat `last_page`/`total_pages`). El worker de pdf.js se importa con `?url` (Vite lo empaqueta como asset).
  - **Texto:** los bloques `texto` se renderizan con `v-html` SIEMPRE pasando por `sanitizeHtml()` (`src/lib/sanitize.ts`, DOMPurify con allow-list; fuerza `rel="noopener noreferrer"` en enlaces). Nunca renderizar `content_body` crudo.
  - El worker de R2 inyecta `Cross-Origin-Resource-Policy: cross-origin` y `Access-Control-Allow-Origin` dinámico para evitar bloqueos por COEP estricto (`require-corp`) del dev server del frontend.


