# PRD Backend — Plataforma de Formación IAM

**Versión:** 1.2
**Fecha:** 2026-06-18
**Stack:** FastAPI (uv) · PostgreSQL (Neon) · Neon Auth (Stack) · Cloudflare R2 · Cloudflare Worker (edge JWT)
**Cliente:** Astro 5 + Vue 3 (`apps/frontend`) — ver `docs/PRD-Frontend.md` v2.1

---

## 🟡 ESTADO DE EJECUCIÓN (snapshot auditado para MVP)

**Avance:** 7 pasos implementados en backend, pero **NO listo para MVP** hasta cerrar remediación P0/P1 de auditoría. Frontend wiring sigue pendiente y debe arrancar después de estabilizar contrato + seguridad backend.

### Hecho técnico

| Paso | Estado | Agente | Detalles |
|---|---|---|---|
| 1-2. Scaffold + modelos + Alembic | ✅ | backend-architect (Sonnet) | `apps/backend/` completo. 11 tablas. Migración manual `c92e06fd8e9f_initial_schema.py`. |
| 3. Neon Auth + RBAC base | ✅ / ⚠️ | security-devops-auditor (Sonnet) | JWKS cache 1h, `verify_stack_token`, `/auth/sync`, `/auth/me`, slowapi 5/min. Falta alias `/me` o ajustar contrato; falta lowercasing email. |
| 4. Catálogo + learning + progress engine | ✅ / ⚠️ | backend-architect (Sonnet) | Cursor pagination, desbloqueo secuencial, exam tema+módulo, repaso forzoso, atorado threshold. R-VID-01 no está garantizado server-side. |
| 5. Media R2 + CF Worker JWT | ✅ / ❌ | backend-architect (Sonnet) | `/media/upload-url` y `/media/play-token` existen. Auditoría detectó IDOR: falta validar enrollment antes de firmar play-token. |
| 6. Admin CRUD + reports + audit | ✅ / ❌ | backend-architect (Sonnet) | CRUD existe, pero RBAC instructor no valida ownership en módulos/temas/preguntas/opciones. Audit log no está probado para todas las mutaciones. |
| 7. Certificados HTML | ✅ | backend-architect (Sonnet) | `POST /issue/{course_id}`, `GET /{uuid}`, público `/verify/{uuid}` Jinja2 + QR data-URI. `PATCH /refresh-name` resuelve R-CERT-04. 10 tests. |

**Verificación auditada (2026-06-18):**
- `cd apps/backend && uv run pytest -q` → **70 passed, 7 warnings**.
- `cd apps/backend && uv run ruff check app tests` → **falla con 14 errores** (imports, line length, unused vars/imports en tests).
- `cd apps/backend && uv run mypy app` → **falla con 2 errores actuales en `app/routers/certificates.py`**, no con los errores antiguos documentados.
- `cd apps/frontend && pnpm run build` → **timeout a 120s**; no confirmado verde.
- `infra/worker` no tiene script `test` ni `build`.

### Pendiente

| Prioridad | Acción | Agente recomendado |
|---|---|---|
| P0. Remediación seguridad backend | Cerrar IDOR media, RBAC owner instructor, `exam_token`, R-VID-01, rate limits, contrato `/me`, lowercasing email | `security-devops-auditor` + `backend-architect` |
| P1. Hardening deploy/tests | `.dockerignore`, worker verification, ruff/mypy clean, cobertura adversarial, audit log completo | `security-devops-auditor` |
| P1. Frontend API client + Stack Auth | `apps/frontend/src/lib/api.ts` tipado, swap `mock.ts` → llamadas reales, Stack Auth SDK en `AuthSplit.vue`, flujo `/auth/sync` con DOB | `vue-ui-architect` |
| P1. Security review final | Re-auditar backend+frontend ya integrados: IDOR, R2 key scoping, R-VID-01, examen, rate limits, leak `is_correct`, CORS/CSRF | `security-devops-auditor` |

### Bloqueadores P0/P1 detectados por auditoría

1. **IDOR en `/api/v1/media/play-token`:** hoy carga `Topic` y llama `compute_topic_state()` sin verificar `Enrollment`. Un usuario autenticado no inscrito puede obtener token si conoce un primer `topic_id` desbloqueable por secuencia. **Fix:** cargar `Topic -> Module -> Course`, exigir `Enrollment(user_id, course_id)`, rechazar archivados, y solo después firmar JWT.
2. **RBAC instructor incompleto:** `modules.py`, `topics.py` y `questions.py` usan `require_role("admin", "instructor")`, pero no validan propiedad del curso. **Fix:** helper común `assert_can_manage_course_resource()` para `course_id`, `module_id`, `topic_id`, `question_id`, `option_id` y reorder.
3. **R-VID-01 no está garantizado server-side:** cliente puede mandar `max_seen_pct=95`. **Fix MVP:** guardar sesión de reproducción (`last_pos`, `last_seen_at`, `duration_seconds`) y rechazar saltos imposibles con tolerancia; calcular avance máximo en servidor. **Fix robusto post-MVP:** receipts firmados por Worker por segmentos vistos.
4. **`exam_token` no se valida:** GET exam emite token, pero POST submit no lo recibe. **Fix:** `ExamSubmitRequest` incluye `exam_token`; token con secreto separado, `aud="exam"`, `exp`, `sub`, `topic_id/module_id`, `question_ids`, `jti`; calificar solo preguntas firmadas y bloquear replay.
5. **Rate limits faltantes en examen:** aplicar `@limiter.limit("10/minute")` a submit de tema y módulo, idealmente por `user_id + topic_id/module_id`.
6. **`media_key` se expone en `TopicView`:** contradice “frontend nunca recibe R2 URL/key”. **Fix:** quitar `media_key` de `/topics/{id}`; entregar media solo vía `/media/play-token`.
7. **Contrato auth drift:** plan dice `/api/v1/me` y `/api/v1/me/logout`; implementación expone `/api/v1/auth/me` y `/api/v1/auth/me/logout`. **Fix MVP:** montar alias `/api/v1/me` y `/api/v1/me/logout` o actualizar frontend+plan; preferir alias por compatibilidad.
8. **Email sin lowercasing DB:** `users.email` es `String(320)` sensible a casing y `/auth/sync` guarda `claims.email` tal cual. **Fix:** normalizar `claims.email.lower()` antes de crear/actualizar y agregar test uppercase.
9. **Examen modular y certificado:** [RESOLVED] `on_module_exam_passed()` no cambia completion; certificado ahora valida que todos los módulos del curso con preguntas de examen final tengan un intento aprobado (`ExamAttempt.passed=True`).
10. **Docker/deploy:** `Dockerfile` usa `COPY . .` sin `.dockerignore`; riesgo de empaquetar `.env`, `.venv`, `.coverage`, caches y `test_*.db`. **Fix:** agregar `.dockerignore` y usuario no-root.
11. **Worker media:** acepta requests sin `Origin/Referer` y token por query string. **Fix MVP:** en prod requerir `Origin/Referer` permitido y aceptar solo `Authorization: Bearer`.
12. **Calidad local:** limpiar `ruff`, `mypy`, scripts de worker y timeout build frontend antes de declarar MVP.

### Estado de archivos clave (verificado)

`apps/backend/app/main.py` registra correctamente los 5 routers (líneas 11-16, 45-49):
- `api_router` con prefix `/api/v1` (auth + catalog + learning)
- `admin_router` (paths internos ya incluyen `/api/v1/admin`)
- `certificates_router` con prefix `/api/v1`
- `media_router` (paths internos `/api/v1/media`)
- `verify_router` público `/verify/{uuid}`

Sin colisiones detectadas en `main.py` tras paralelización de pasos 5+6+7.

### Issues conocidos / deuda técnica no bloqueante

1. **`db.py` engine global:** `pool_size`/`max_overflow` hardcodeados; tests SQLite mitigan en `conftest.py`. Refactor opcional.
2. **CITEXT no activado:** `users.email` es `String(320)`; para case-insensitive a nivel DB usar `CREATE EXTENSION citext;` y migrar columna. Para MVP, lowercasing en app + test uppercase.
3. **JSONB vs JSON:** modelos usan `JSON` portable; migración usa `JSONB` en Postgres. Alinear si se requiere `alembic autogenerate` limpio o búsqueda GIN real.
4. **UUID:** `new_uuid()` usa UUIDv4 aunque el plan original pedía UUIDv7. No bloquea MVP; decidir antes de producción con datos reales.
5. **Worker JWT secret rotation:** sin KMS. Documentar runbook de rotación manual.
6. **Auto-emisión de certificado:** hoy es manual desde frontend (`POST /issue/{course_id}` cuando ve 100%). Mantener MVP, pero validar requisito de examen modular.

### Decisiones cerradas (no revisitar)

- ✅ Pagos: gratis, solo auth.
- ✅ Roles: admin + instructor + estudiante.
- ✅ Examen: por tema **+** final de módulo (XOR en `questions.topic_id`/`module_id`).
- ✅ Certificado: HTML público `/verify/{uuid}` + QR. **NO PDF.**
- ✅ R-CERT-04: snapshot al emitir + `PATCH /refresh-name` para owner.
- ✅ Video: client FFmpeg.wasm faststart → presigned PUT R2 → Worker valida JWT HS256 → Range requests. Anti-hotlink por Origin/Referer.
- ✅ Idioma: solo español MVP.
- ✅ Progresión: estricta secuencial (tema anterior aprobado → siguiente disponible; módulo anterior + su exam → siguiente módulo).

### Para arrancar nueva sesión

```bash
cd /home/leo/Desktop/iam/apps/backend
uv sync                                    # asegura deps
uv run pytest -q                           # esperado actual: 70 passed
uv run ruff check app tests                # debe quedar clean antes de MVP
uv run mypy app                            # debe quedar clean antes de MVP
```

Orden de arranque recomendado:
1. Cerrar bloqueadores P0 backend y agregar pruebas adversariales.
2. Dejar `pytest`, `ruff` y `mypy` verdes.
3. Recién entonces arrancar frontend wiring con `vue-ui-architect`.

Brief frontend debe incluir:
- Stack actual frontend (Astro 5.7 + Vue 3.5 + Pinia 2.3 + Tailwind 4.1 + Zod 3.24).
- Contrato backend documentado en este plan §5 + endpoints implementados.
- Reemplazar `apps/frontend/src/lib/mock.ts` por cliente HTTP (`api.ts`) con tipos generados de OpenAPI (`http://localhost:8000/openapi.json`).
- Integrar Stack Auth client SDK (`@stackframe/stack`) en `AuthSplit.vue` y flujo `/auth/sync` con captura de `birth_date` post-login.
- Componentes: `LearningPlayer.vue` (consumir `/media/play-token` + envío Bearer JWT al Worker), `ExamRunner.vue` (consumir `/topics/{id}/exam` + submit).
- Stores Pinia: `user`, `catalog`, `progress`.

Después del frontend: paso 12 security review final con `security-devops-auditor`.

---

---

## 1. Context

El frontend (`apps/frontend`) está scaffolded con mocks (`src/lib/mock.ts`) y rutas completas estudiante + admin. No existe backend ni cliente HTTP. El PRD frontend v2.1 define 24 pantallas, reglas de negocio R-AUTH/R-CAT/R-PROG/R-VID/R-EX/R-CERT/R-ADM y límites de campos.

Este backend levanta el contrato API que consume el frontend, persiste contenido y progreso, integra Neon Auth como IdP, y entrega media vía R2 con validación edge (Cloudflare Worker + JWT corto).

**Decisiones del fundador que sobreescriben PRD frontend v2.1:**
| Decisión | PRD v2.1 | Hoy (vincula este backend) |
|---|---|---|
| Roles | admin + estudiante | **admin + instructor + estudiante** |
| Examen | solo por tema | **por tema + final de módulo** |
| Certificado | PDF descargable | **HTML público compartible (URL `/verify/{uuid}`)** |
| Auth | `@auth/core` Google + pwd | **Neon Auth (Stack Auth) — Google + email/pwd** |
| Video delivery | Vue-Plyr genérico | **Client FFmpeg.wasm faststart → presigned PUT a R2 → CF Worker valida JWT → Range requests** |
| Pagos | fuera de alcance | igual (gratis, solo auth) |
| i18n | español | igual (español único) |

Resto del PRD frontend v2.1 se mantiene como objetivo. La auditoría detectó que R-VID-01 y R-EX server-side aún requieren hardening antes de MVP.

---

## 2. Stack y entorno

- **Runtime:** Python 3.12, `uv` para venv/lock (`uv venv && uv sync && uv run uvicorn app.main:app --reload`).
- **Framework:** FastAPI 0.115+, Pydantic v2, uvicorn.
- **DB:** Neon PostgreSQL (serverless), SQLAlchemy 2.x async + asyncpg, Alembic migraciones.
- **Auth:** Neon Auth (Stack Auth) — valida JWT del proveedor (JWKS público) en middleware. No se almacenan contraseñas localmente.
- **Storage:** Cloudflare R2 (S3-compatible) vía `boto3` o `aioboto3` para presigned URLs (PUT y GET).
- **Edge JWT:** PyJWT (HS256 con secret compartido con CF Worker) — el Worker valida; el backend firma.
- **Email (reporte semanal):** resend.com (opcional MVP, stub).
- **Tests:** pytest + httpx AsyncClient + pytest-asyncio.
- **Lint/format:** ruff + mypy strict.
- **Deploy:** Docker → Railway.

---

## 3. Estructura de carpetas (nueva: `apps/backend/`)

```
apps/backend/
├── pyproject.toml            # uv
├── uv.lock
├── Dockerfile
├── .dockerignore             # requerido antes de deploy
├── .env.example
├── alembic.ini
├── alembic/
│   └── versions/
├── app/
│   ├── main.py               # FastAPI app, CORS, routers, lifespan
│   ├── config.py             # Settings via pydantic-settings
│   ├── db.py                 # AsyncEngine + session factory
│   ├── deps.py               # get_db, get_current_user, require_role
│   ├── security/
│   │   ├── neon_auth.py      # JWKS fetch + validation Stack Auth
│   │   └── media_jwt.py      # firma HS256 para CF Worker
│   ├── models/               # SQLAlchemy
│   │   ├── user.py
│   │   ├── course.py         # Curso, Modulo, Tema
│   │   ├── question.py       # Pregunta, Opcion
│   │   ├── progress.py       # Inscripcion, ProgresoTema, IntentoExamen
│   │   └── certificate.py
│   ├── schemas/              # Pydantic
│   ├── crud/                 # repos
│   ├── routers/
│   │   ├── auth.py           # /me, /webhook (Neon Auth)
│   │   ├── catalog.py        # /cursos (estudiante)
│   │   ├── learning.py       # /cursos/{id}/inicio, /temas/{id}/progreso, /examen
│   │   ├── certificates.py   # /certificados/{uuid}, /verify/{uuid}
│   │   ├── media.py          # /media/upload-url, /media/play-token
│   │   └── admin/
│   │       ├── courses.py
│   │       ├── modules.py
│   │       ├── topics.py
│   │       ├── questions.py
│   │       ├── students.py
│   │       └── reports.py
│   └── services/
│       ├── progress_engine.py    # desbloqueo secuencial, % curso
│       ├── exam_engine.py        # randomización, score, repaso forzoso
│       └── r2.py                 # presigned PUT/GET
└── tests/
```

---

## 4. Modelo de datos (PostgreSQL)

Convención: `id` UUID v7, `created_at`/`updated_at` `timestamptz`. Soft-delete con `archived_at` solo donde aplica.

### 4.1 Usuarios (sincronizados con Neon Auth)
```
users(
  id UUID PK,
  neon_user_id TEXT UNIQUE NOT NULL,   -- sub del JWT Stack Auth
  email CITEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  birth_date DATE NOT NULL,             -- R-AUTH-04 edad ≥13
  role TEXT NOT NULL CHECK (role IN ('admin','instructor','estudiante')) DEFAULT 'estudiante',
  status TEXT DEFAULT 'nuevo',          -- nuevo|activo|completado|atorado (R-EST 6.1)
  created_at, updated_at
)
```
Sincronización: endpoint `/auth/sync` o webhook Stack Auth crea/actualiza `users`. Si no existe en login → 409 con `setup_required` para forzar formulario con `birth_date` (Neon Auth no captura DOB).

### 4.2 Contenido
```
courses(id, slug UNIQUE, title, short_desc, long_desc, cover_key,
        age_min, age_max, order_index, status TEXT CHECK IN ('borrador','publicado','archivado'),
        instructor_id FK users, created_at, updated_at)

modules(id, course_id FK CASCADE, title, description, order_index, archived_at)

topics(id, module_id FK CASCADE, title, content_type TEXT CHECK IN ('video','pdf','imagen','texto'),
       content_body TEXT,            -- para tipo 'texto' (markdown)
       media_key TEXT,               -- R2 key para video/pdf/imagen
       duration_seconds INT,         -- video
       has_exam BOOLEAN DEFAULT TRUE,
       exam_min_score INT DEFAULT 70 CHECK (50..100),  -- R-EX-07
       order_index, archived_at)

questions(id, topic_id FK CASCADE NULL, module_id FK CASCADE NULL,  -- una de las dos
          enunciado TEXT, archived_at,
          CHECK ((topic_id IS NULL) <> (module_id IS NULL)))
-- Soporta examen por tema Y examen final de módulo (decisión nueva)

options(id, question_id FK CASCADE, texto TEXT, is_correct BOOLEAN, order_index)
```

### 4.3 Progreso
```
enrollments(id, user_id, course_id, started_at, completed_at,
            UNIQUE(user_id, course_id))

topic_progress(id, user_id, topic_id,
               state TEXT,                    -- bloqueado|disponible|contenido_visto|aprobado|en_repaso
               video_last_pos_seconds INT,    -- R-VID-03 reanudación
               video_max_seen_pct INT,        -- nunca decrece, gate del 95%
               pdf_last_page INT,
               pdf_total_pages INT,
               content_completed_at TIMESTAMPTZ,
               UNIQUE(user_id, topic_id))

exam_attempts(id, user_id,
              topic_id FK NULL, module_id FK NULL,  -- una de las dos
              score INT, passed BOOLEAN,
              min_score_snapshot INT,        -- R-ADM-05: snapshot al intento
              answers JSONB,                 -- {question_id: option_id}
              created_at)
```

### 4.4 Certificados
```
certificates(id, uuid UUID UNIQUE NOT NULL,   -- URL pública /verify/{uuid}
             user_id, course_id, issued_at,
             student_name_snapshot TEXT,      -- R-CERT-04 nombre al emitir (NOTA: PRD frontend dice "al momento de descarga"; backend hoy usa snapshot al issue, exponer endpoint para refresh manual si se requiere)
             course_title_snapshot TEXT,
             UNIQUE(user_id, course_id))
```

### 4.5 Auditoría mínima
```
admin_audit(id, actor_id, action, entity, entity_id, payload JSONB, created_at)
```

**Índices clave:** `(user_id, topic_id)` en `topic_progress`, `(course_id, order_index)` en `modules`, `(module_id, order_index)` en `topics`, GIN en `audit.payload`.

---

## 5. API — contrato (prefijo `/api/v1`)

### 5.1 Auth & Perfil
| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| POST | `/auth/sync` | Bearer Stack Auth | Crea/actualiza `users` desde JWT + body con `birth_date` y `full_name`. Devuelve perfil. |
| GET | `/me` | user | Perfil + rol + status |
| POST | `/me/logout` | user | (opcional, Stack maneja sesión) |

R-AUTH-04: rechaza si edad <13 con 422 `{code:"under_age"}`.

### 5.2 Catálogo (estudiante)
| GET | `/courses` — filtra por edad usuario (R-CAT-01) + status=`publicado` o (`archivado` + enrolled). Soporta `?cursor` para scroll infinito de 12. |
| GET | `/courses/{slug}` — detalle + módulos + temas (sin respuestas). |
| POST | `/courses/{slug}/enroll` — crea `enrollments` (idempotente). R-PROG-01. |
| GET | `/courses/{slug}/progress` — % total + estado por tema. |

### 5.3 Aprendizaje
| GET | `/topics/{id}` — devuelve contenido + estado del usuario. Si `state=bloqueado` → 403. |
| POST | `/topics/{id}/heartbeat` — `{type:'video', pos_seconds, max_seen_pct}` o `{type:'pdf', last_page}`. Server guarda max monotónico. |
| POST | `/topics/{id}/mark-content-done` — server valida ≥95% video / última página PDF / 90% texto / 5s+scroll imagen → transición `contenido_visto`. |
| GET | `/topics/{id}/exam` — devuelve preguntas randomizadas (R-EX-02/03), sin marcar correctas. Requiere `contenido_visto`. |
| POST | `/topics/{id}/exam/submit` — `{answers: [{question_id, option_id}]}` → score, passed, min_score. Si falla → marca `en_repaso` y resetea `video_max_seen_pct=0` (R-EX-08). |
| GET | `/modules/{id}/exam` + `/modules/{id}/exam/submit` — análogo, gate para desbloquear siguiente módulo. |

### 5.4 Media (R2 + edge JWT)
| POST | `/media/upload-url` — body `{filename, content_type, scope:'video'|'pdf'|'imagen'|'cover'}`. Solo admin/instructor. Devuelve `{put_url, key}` presigned 10 min. |
| POST | `/media/play-token` — body `{topic_id}`. Backend valida que el usuario tenga `state ∈ {disponible, contenido_visto, aprobado, en_repaso}` para ese tema → firma JWT HS256 con `{sub:user_id, key:media_key, exp:+15min}`. Frontend usa `Authorization: Bearer <jwt>` en request al Worker (que valida y proxy al R2 con Range). |

Frontend nunca recibe la R2 URL pública. El Worker es la única ruta de delivery (anti-hotlink).

### 5.5 Certificados
| POST | `/certificates/issue/{course_id}` — server valida 100% del curso, crea row (idempotente). |
| GET | `/certificates/{uuid}` (auth opcional) — JSON con metadata para render frontend. |
| GET | `/verify/{uuid}` — público, página HTML server-rendered (Jinja2 simple) con datos + QR code. |

### 5.6 Admin (`/admin/*` requiere `role=admin`; instructor solo CRUD de sus cursos)
- CRUD `courses`, `modules`, `topics`, `questions`, `options`.
- `POST /admin/courses/{id}/publish` (R-ADM-02: no permite delete con inscritos, solo `archive`).
- `GET /admin/students` con filtros (status, fecha registro, atorado).
- `GET /admin/students/{id}` con cursos + progreso + intentos.
- `GET /admin/reports/export?type=...` → CSV streaming.
- `GET /admin/dashboard` — KPIs agregados (counts + ratios).

**RBAC dependency:** `Depends(require_role('admin'))` y `require_owner_or_admin(course)` para instructor.

---

## 6. Reglas críticas del motor de progreso

`app/services/progress_engine.py`:

1. **Desbloqueo secuencial (R-PROG-02):** un tema `disponible` requiere que el tema con `order_index - 1` en el mismo módulo esté `aprobado` (o que sea el primero del primer módulo del curso, o que el módulo anterior esté completo + examen modular aprobado).
2. **Content completion server-side:** server nunca confía en frontend. `mark-content-done` recalcula desde `topic_progress.video_max_seen_pct` y compara con tipo de contenido.
3. **Repaso forzoso (R-EX-08):** fallar examen → `state='en_repaso'`, `video_max_seen_pct=0`, `pdf_last_page=0`. Endpoint `exam` bloqueado hasta re-completion.
4. **% curso (R-PROG-04):** `(temas aprobados / total temas no archivados) * 100`, redondeo entero. Cachear en `enrollments.progress_cached` con invalidación en submit.
5. **Status del estudiante (6.1 PRD):** job batch o trigger DB calcula `atorado` = ≥3 intentos fallidos consecutivos en el mismo tema.

---

## 7. Seguridad

- **CORS:** origin allowlist desde `FRONTEND_URL` env.
- **Rate limiting:** `slowapi` por IP en `/auth/*` (5/min) y `/exam/submit` (10/min).
- **Idempotency keys** en mutaciones de progreso (header `Idempotency-Key`).
- **Audit log:** todo `admin/*` POST/PATCH/DELETE → `admin_audit`.
- **Media JWT:** secret rotable, exp 15 min, `aud='r2-worker'`, scope al `media_key` específico.
- **Validación strict** Pydantic con límites del PRD frontend §5.1.
- **Edad:** server recalcula desde `birth_date`; ignora `age` del cliente.
- **Snapshot de `min_score`** en `exam_attempts` (R-ADM-05).

---

## 8. Variables de entorno (`.env.example`)

```
DATABASE_URL=postgresql+asyncpg://...neon.tech/...
STACK_PROJECT_ID=...
STACK_SECRET_SERVER_KEY=...
STACK_JWKS_URL=https://api.stack-auth.com/.../jwks
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=iam-media
R2_PUBLIC_BASE=https://media.iam.example  # CF Worker hostname
MEDIA_JWT_SECRET=...                       # compartido con Worker
FRONTEND_URL=https://app.iam.example
RESEND_API_KEY=...                          # opcional
```

---

## 9. Pasos de implementación (orden de ejecución actualizado para MVP)

Delegación recomendada (orquestador → subagentes):

1. **`backend-architect`** → scaffolding `apps/backend/`, pyproject (uv), Dockerfile, alembic init, `app/main.py` con CORS + health.
2. **`backend-architect`** → modelos SQLAlchemy + Alembic migración inicial (`users`, `courses`, `modules`, `topics`, `questions`, `options`, `enrollments`, `topic_progress`, `exam_attempts`, `certificates`, `admin_audit`).
3. **`security-devops-auditor`** → integración Neon Auth (JWKS fetch + cache, dependency `get_current_user`), `/auth/sync` con validación DOB ≥13, RBAC `require_role`.
4. **`backend-architect`** → routers catálogo + aprendizaje + `progress_engine` con tests.
5. **`backend-architect`** → media: `/upload-url` (presigned PUT R2) + `/play-token` (HS256), boilerplate CF Worker en `infra/worker/`.
6. **`backend-architect`** → admin CRUD + reportes CSV streaming + audit log.
7. **`backend-architect`** → certificados (endpoint emisión + `/verify/{uuid}` Jinja2 + QR via `qrcode[pil]`).
8. **`security-devops-auditor` + `backend-architect`** → remediación P0 backend:
   - Validar enrollment en `/api/v1/media/play-token`.
   - Validar ownership de instructor en modules/topics/questions/options/reorder.
   - Implementar `exam_token` obligatorio en submit y calificar solo `question_ids` firmadas.
   - Implementar rate limit `10/minute` en submits.
   - Endurecer R-VID-01 con avance server-side anti-salto.
   - Quitar `media_key` de `TopicView`.
   - Añadir alias `/api/v1/me` y `/api/v1/me/logout` o actualizar contrato.
   - Lowercase de email en `/auth/sync`.
9. **`security-devops-auditor`** → hardening deploy/edge:
   - `.dockerignore`, usuario no-root en Dockerfile.
   - Worker solo `Authorization: Bearer`; rechazar query token.
   - Worker prod rechaza requests sin `Origin/Referer` permitido.
   - Scripts `build`/`typecheck`/`test` o verificación mínima Worker.
10. **`backend-architect`** → pruebas adversariales y limpieza:
   - Tests P0/P1 listados en §10.
   - `uv run pytest -q`, `uv run ruff check app tests`, `uv run mypy app` verdes.
11. **`vue-ui-architect`** → `apps/frontend/src/lib/api.ts` cliente HTTP tipado, swap de `mock.ts` por llamadas reales, Stack Auth client SDK en `AuthSplit.vue`, stores Pinia `user/catalog/progress`, `LearningPlayer` con `/media/play-token`, `ExamRunner` con examen backend.
12. **`security-devops-auditor`** → revisión paranoica final backend+frontend (IDOR, R2 JWT scope, R-VID-01, R-EX, rate limits, leak `is_correct`, CORS/CSRF).

---

## 10. Verificación end-to-end

```bash
# 1. levantar
cd apps/backend && uv venv && uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000

# 2. smoke
curl http://localhost:8000/health
curl http://localhost:8000/docs   # OpenAPI

# 3. tests
uv run pytest -xvs
uv run ruff check app tests
uv run mypy app

# 4. flujo manual desde frontend
cd ../frontend && pnpm install && pnpm run build && pnpm dev
# Login → sync DOB → catálogo (filtrado por edad) → enroll → ver video con CF Worker JWT → submit examen → repaso forzoso si falla → emitir certificado → /verify/{uuid}
```

**Criterios de aceptación:**
- [ ] `uv run pytest -q`, `uv run ruff check app tests` y `uv run mypy app` verdes.
- [ ] Frontend `pnpm run build` verde sin depender de `src/lib/mock.ts` para flujos reales.
- [ ] Worker tiene verificación local (`npm run build` o `npm run typecheck`) y pasa.
- [ ] Estudiante menor de 13 rechazado en `/auth/sync`.
- [ ] `/auth/sync` normaliza email a lowercase y test uppercase no duplica usuarios por casing.
- [ ] `/api/v1/me` y `/api/v1/me/logout` existen o el contrato frontend documenta `/api/v1/auth/me` explícitamente.
- [ ] Tema bloqueado devuelve 403 incluso si el usuario fuerza el endpoint.
- [ ] R-VID-01: salto imposible de progreso (`0 → 95%` en una request) no permite `mark-content-done`.
- [ ] `video_max_seen_pct` nunca decrece y se calcula/valida server-side.
- [ ] `GET /topics/{id}` no expone `media_key`.
- [ ] `play-token` rechaza usuario no inscrito, tema archivado, tema bloqueado y media inexistente.
- [ ] Worker rechaza path que no coincide con `key`, origin no permitido, ausencia de origin en prod y token por query string.
- [ ] `GET /topics/{id}/exam` no expone `is_correct`.
- [ ] `POST /exam/submit` exige `exam_token` válido, no expirado, no replay, con `question_ids` firmadas.
- [ ] Submit rechaza `option_id` que no pertenece a `question_id`.
- [ ] `POST /topics/{id}/exam/submit` y `/modules/{id}/exam/submit` devuelven 429 al exceder rate limit.
- [ ] Examen falla → estado `en_repaso` y `video_max_seen_pct=0`.
- [x] Si hay examen modular, certificado requiere módulo aprobado además de temas aprobados.
- [ ] Certificado solo emite al 100% de temas no archivados.
- [ ] `/verify/{uuid}` renderiza sin auth y muestra QR.
- [ ] Instructor no puede crear/editar/borrar/reordenar módulos, temas, preguntas u opciones de cursos ajenos.
- [ ] `admin_audit` registra toda mutación admin: courses, modules, topics, questions, options, publish/archive/reorder/delete.
- [ ] Docker build no incluye `.env`, `.venv`, `.coverage`, caches ni `test_*.db`; contenedor corre como usuario no-root.

---

## 11. Fuera de alcance (este backend, MVP)

- Pagos / Stripe (decisión: gratis).
- Notificaciones push.
- Multi-tenant real (single org).
- i18n contenido.
- Generación PDF de certificado (decisión: HTML).
- Foros, chat instructor, gamificación, impersonación admin.
- App nativa.

## 12. Riesgos abiertos

- **R-VID-01 server-side:** MVP debe bloquear saltos obvios; protección criptográfica por segmentos queda post-MVP si el costo es alto.
- **Exam session replay:** requiere `jti` y almacenamiento/TTL para evitar reuso. Si se omite en MVP, documentar riesgo y limitar intentos.
- **Conflicto R-CERT-04:** resuelto por snapshot al issue + `PATCH /certificates/{uuid}/refresh-name` owner-only antes de compartir/mostrar.
- **Worker JWT secret rotation:** sin KMS en MVP, rotación manual. Documentar runbook y ventana de doble secreto si se requiere cero downtime.
- **Quota R2:** sin transcoding, videos crudos pesan; coordinar límite 500 MB con admin y monitor de uso.
- **Stack Auth lock-in:** verificar costo/latencia JWKS vs alternativas (Clerk, Supabase Auth) — decisión del fundador, mantener.
- **Astro dynamic routes:** frontend actual usa `getStaticPaths()` con mocks. Para backend real decidir SSR/adaptador o mover carga a islas cliente antes de reemplazar `mock.ts`.
