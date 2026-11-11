# QA local — primera pasada (2026-11-05)

Entorno: `compose.local.yaml` (Postgres local, backend, Vite, bucket S3 local + gateway que replica el worker de Cloudflare). Auth mock. R2 de producción NO usado.
Método: agent-browser (UI estudiante/admin) + pruebas directas a la API (httpx). Screenshots en `docs/qa-local/screenshots/`.
Numeración de tickets continúa la auditoría previa (IAM-001..003).

## Críticos

### IAM-004 — Clase con examen activo y 0 preguntas = callejón sin salida (bloqueante)
- `TopicCreate.has_exam` es `true` por defecto y el curso se puede publicar con temas así.
- Estudiante: "Marcar como completado" → `GET /topics/{id}/exam` responde 404 `No exam questions for this topic`; la UI no muestra error ni navega. Estado queda `contenido_visto` para siempre → curso nunca llega a 100% → no hay certificado.
- Repro: admin crea tema (sin tocar el checkbox de examen) sin preguntas, publica curso; estudiante inscrito completa la clase anterior y abre esa. Evidencia: `screenshots/12-t2.png`.
- Fix sugerido: (a) bloquear `publish` si algún tema con `has_exam` tiene < 1 pregunta (422 con lista), (b) default `has_exam=false`, (c) la UI debe mostrar el error del examen.

### IAM-005 — El gating de completado lo afirma el cliente (se completa curso y certificado con 4 requests)
- `POST /topics/{id}/heartbeat` acepta `last_page=99,total_pages=1` (last_page > total_pages) y `total_pages` enviado por el cliente (no se compara con el PDF real). Video: `pos_seconds`, `duration_seconds`, `max_seen_pct=100` aceptados en un solo request sin reproducir nada.
- Repro (API): heartbeat video 100% → `mark-content-done` 200 → examen → `POST /certificates/issue/{course}` 201, todo en < 1 s.
- Impacto: el certificado deja de significar que el alumno vio el contenido (contradice el diseño de CLAUDE.md "gating en server").
- Fix sugerido: guardar `total_pages` server-side al guardar el bloque (pdf.js/pypdf al subir), rechazar `last_page > total_pages`, limitar avance por tiempo real (delta de pos ≤ delta de reloj × 1.5 entre heartbeats; tiempo mínimo por página), usar solo `duration_seconds` del bloque.

### IAM-006 — Rate limit de `/auth/sync` por IP del proxy: todos los usuarios comparten 5/min en producción
- `slowapi` con `get_remote_address`; `infra/vps` corre uvicorn detrás de Caddy sin `--proxy-headers --forwarded-allow-ips`. Verificado local: peticiones con distinto `X-Forwarded-For` comparten el mismo bucket (429 para todas).
- Impacto: en un registro masivo (retiro, catequesis, clase en grupo) el 6.º alumno del minuto recibe 429 y no puede registrarse.
- Fix sugerido: `uvicorn ... --proxy-headers --forwarded-allow-ips='*'` (solo si el puerto del backend no está expuesto fuera de Docker) o key_func por `sub` del token; ajustar límite. Verificar en el VPS real.

## Altos

### IAM-007 — PDF requerido imposible de completar con viewport bajo
- `ContentBlockPlayer.vue:202` `IntersectionObserver threshold: 0.5` sobre cada canvas, dentro de contenedor `max-h-[80vh]`. Página PDF ≈ 993 px; si el contenedor mide < ~497 px (viewport < ~620 px de alto: móvil horizontal, zoom 200%, ventanas pequeñas) ninguna página llega al 50% visible y la lectura se queda en pág. 1/N.
- Repro: viewport 1280×577 → se queda en 1/3 (ver `08-pdf-fin.png`); 1280×900 → 3/3 (`09-pdf-ok.png`).
- Fix: observar con umbral por altura visible (`rootMargin`, o `threshold: [0, .25]` + comparar contra `min(0.5, containerHeight / pageHeight)`).

### IAM-008 — Dashboard admin muestra métricas inventadas
- `AdminDashboard.vue` (~l.121): "Cuellos de botella" con "Examen Final - Módulo 2 · 65% reprueban", actividad "María González obtuvo su certificado", "Rendimiento de módulos" (120/85/43 activos), "142 certificados emitidos +28 este mes", deltas "+12 este mes", etc. DB local: 1–3 estudiantes, 1 certificado. Mismo patrón que CODE-001 de la auditoría previa. Evidencia: `02-admin.png`.
- Fix: conectar a `/admin/dashboard` o ocultar las tarjetas sin datos reales.

## Medios / bajos (agrupar en un ticket)
- **IAM-009 (medio)** `PUT /admin/topics/{id}/blocks` acepta `media_key` inexistente (404 recién al estudiante), `pdf/../cover/x` y keys de 3000 caracteres. `POST /media/upload-url` valida solo el `content_type` declarado; no hay límite de tamaño ni magic bytes server-side (los límites "50 MB / 500 MB" son solo texto de la UI). Viola estándar de uploads.
- **IAM-010 (bajo)** Sin Authorization → 422 (`header authorization required`) en vez de 401; el 429 de slowapi responde `{"error": "..."}` y no el contrato `{"error": {"code","message"}}`.
- **IAM-011 (bajo)** Las preguntas se crean todas con `order_index=0` (orden de examen no determinista).
- **IAM-012 (bajo)** Subtítulo de clase muestra `s · Con examen` cuando `duration_seconds` es null (`07-leccion.png`).
- **IAM-013 (bajo)** `GET /topics/{id}` devuelve `media_key` de cada bloque al estudiante (CLAUDE.md dice ocultarlo en catálogo; aquí sí sale, protegido igual por play-token).
- **IAM-014 (bajo)** `seed_e2e.py` crea una clase sin bloques (viola "≥1 bloque") y usa `create_all`; actualizar.

## Verificado OK
Estudiante → endpoints admin 403; no inscrito → 403; clase bloqueada 403 en topic/heartbeat/mark-done/exam/play-token; borrador invisible (404) y no inscribible; `alg:none` y token de examen ajeno rechazados; `/auth/sync` ignora `role` del body; play-token solo con inscripción+desbloqueo; gateway: sin token 401, key distinta 403, Range 206; certificado público `/verify/{uuid}` ok; flujo UI completo: login mock → inscribir → PDF (pdf.js) → examen → aprobado; subida admin directa al bucket local con CORS.

## No cubierto aún
Reproducción real de video en `<video>` (requiere archivo de video), audio/imagen, eliminar/archivar en admin, reportes/export, estudiantes admin, responsive móvil, login real con Neon Auth, correos Resend, descarga del certificado PDF, concurrencia de examen (doble submit).

---

# Segunda pasada — flujo de guardado de preguntas y texto (2026-11-05)

Código revisado: `AdminTemaDetalle.vue`, `AdminPreguntaDetalle.vue`, `RichTextEditor.vue`, `sanitize.ts`, `routers/admin/questions.py`, `ExamRunner.vue`, `ContentBlockPlayer.vue`. Todo lo siguiente fue reproducido en vivo salvo indicación.

### IAM-015 (crítico) — Cada "Guardar" del tema borra el avance de todos los alumnos
`handleSave` llama siempre a `PUT /topics/{id}/blocks`, que borra y recrea los bloques (y su `ContentBlockProgress`) y devuelve a `disponible` a todo alumno no `aprobado`. Aunque el admin solo corrija una errata en una pregunta o el título. Repro API: s2 con PDF 3/3 y `contenido_visto` → PUT de bloques idénticos → `pdf_last_page=0`, estado `disponible`. Además el guardado son 3 llamadas secuenciales no atómicas (topic → blocks → questions): si la 3.ª falla (422), los bloques ya se reescribieron y el progreso ya se perdió.
Fix: no enviar bloques si no cambiaron; el backend debe hacer upsert por `id` conservando progreso; endpoint único transaccional.

### IAM-016 (crítico) — El guardado de preguntas recrea todas las preguntas/opciones y puede perder el banco
- `POST /topics/{id}/questions/bulk` archiva todas y crea nuevas: **todos los IDs cambian** en cada guardado (overlap 0). Un alumno con examen abierto recibe `403 invalid_exam_token` al enviar y pierde sus respuestas; el historial de intentos queda apuntando a preguntas archivadas.
- Desmarcar "Requiere cuestionario" y guardar llama bulk con `[]` → archiva todo el banco sin aviso.
- `has_exam=true` con 0 preguntas se guarda sin error (origen de IAM-004 también desde la UI).
- `normalizeQuestion` marca en silencio la primera opción como correcta si la BD no tiene ninguna (oculta corrupción).
Fix: upsert por `id` (como ya hace `PATCH /questions/{id}`), no archivar al desmarcar examen, validar ≥1 pregunta si `has_exam`.

### IAM-017 (alto) — `PATCH /admin/options/{id}` rompe "exactamente 1 correcta"
Marcar otra opción como correcta deja 2 correctas; desmarcar todas deja 0 (pregunta imposible de aprobar). Reproducido: 2 y 0 correctas. La UI actual no usa este endpoint, pero está expuesto a admin/instructor.
Fix: eliminar el endpoint o validar el invariante al final de la transacción.

### IAM-018 (medio) — Enunciados con formato: el banco admin muestra HTML crudo y las validaciones no coinciden
- `AdminPreguntas.vue:69` y `AdminModuloDetalle.vue:228` pintan `{{ p.enunciado }}`: se ve `<p>¿Pregunta <strong>0</strong>…</p>` (`screenshots/14-admin-lista-preguntas.png`). El alumno sí lo ve bien (sanitizado).
- Ayuda del editor de banco dice "5-300 caracteres"; backend/otra pantalla permiten 5000, y el mínimo cuenta etiquetas HTML (`<p>a</p>` pasa con 1 carácter real).
Fix: renderizar con `sanitizeHtml` o texto plano; validar longitud sobre texto sin HTML y unificar límites.

### IAM-019 (medio) — El editor produce formato que el sanitizador elimina
`StarterKit` permite blockquote, code, strike y hr (atajos `> `, `` ` ``, `---`); el allow-list de `sanitize.ts` y del propio editor solo conserva `p,br,strong,em,h2,h3,ul,ol,li,a`. Resultado: el admin ve una cita/código y el alumno ve texto plano (`15-texto-formato.png`: "cita", "cod tach"); al reabrir el editor también se pierde. XSS probado: seguro (`onerror`, `javascript:`, `<script>`, `<iframe>`, `<style>` no se ejecutan).
Fix: configurar `StarterKit` con solo los nodos permitidos.

### IAM-020 (medio) — Bloques de texto vacíos aceptados
`<p></p>` y `<p><br></p>` pasan la validación de UI (`!content_body.trim()`) y de API (solo rechaza espacios). El alumno ve una tarjeta vacía "TEXTO · Complementario".
Fix: validar sobre texto plano (UI: `editor.isEmpty`; API: strip HTML).

### IAM-021 (medio) — Tras "Marcar como completado" en clase solo-texto el botón no cambia
La clase pasa a `contenido_visto` en el servidor, pero la pantalla sigue mostrando "Marcar como completado" hasta recargar; recién entonces aparece "Ir al Examen".
Fix: actualizar el estado local con la respuesta de `mark-content-done`.
