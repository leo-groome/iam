# QA IAM — Tickets: qué funciona y qué no

Fecha: 5 de noviembre de 2026
Entorno: local con Docker (Postgres, backend, frontend, bucket S3 local que replica el worker de Cloudflare). Auth simulada (mock). No se tocó producción ni el bucket real.
Método: agent-browser (UI de estudiante y admin) + pruebas directas a la API.
Numeración: continúa la auditoría previa (IAM-001 a IAM-003). Evidencia en `docs/qa-local/screenshots/`; archivo para importar a Linear: `docs/qa-local/linear-import.csv`.

## Estado de correcciones (2026-11-05)

Los 18 tickets (IAM-004 a IAM-021) tienen fix en el working tree, sin commitear. Backend: 137 tests pasan. Frontend: `pnpm build` ok.

**Verificado por tests:** 004, 005 (lógica + heartbeat), 009, 010, 011, 015, 016, 017, 018 (API), 020.
**Pendiente de verificar a mano:**
- IAM-005: migración `h6d7e8f9a0b1` (SQL generado, no corrida contra Postgres); el conteo de páginas con pypdf contra el bucket real; el reintento de heartbeat de PDF en pantalla.
- IAM-006: confirmar en el VPS que `172.29.0.0/24` (subred fija en `infra/vps/compose.yaml`) no choca con otra red del host, y que el 6.º registro del minuto ya no recibe 429.
- IAM-007, 008, 012, 018 (UI), 019, 021: repro visual con agent-browser (viewport 1280×577 para 007).
- IAM-009: `Content-Length` firmado en la URL de subida; probar subida real desde el admin (video con faststart cambia el tamaño: se envía el del archivo final).

**Cambios de contrato:** `POST /media/upload-url` exige `size_bytes`; `PATCH /admin/options/{id}` eliminado; `ContentBlockIn` acepta `id`; `GET /topics/{id}` ya no devuelve `media_key`; `TopicCreate.has_exam` ahora es `false` por defecto; `publish` responde 422 `exam_without_questions`; el 429 usa `{"error": {"code", "message"}}`.

## Hallazgos de validación manual (2026-11-05)

#### IAM-022 — Completar un PDF requerido no permite avanzar al examen
- **Prioridad:** Alto
- **Falla:** en la clase `Tema 1` (PDF requerido de 3 páginas y examen activo), el visor llega a `pág. 3/3` y habilita **Marcar como completado**. Al pulsarlo, la interfaz permanece sin cambios: sigue mostrando el mismo botón y no aparece **Ir al Examen**. Tras recargar, el estado sigue igual.
- **Impacto:** el alumno no puede presentar el examen ni continuar con el curso.
- **Repro:** iniciar sesión como estudiante de prueba; abrir `QA Curso` → `Tema 1`; con viewport 1280×577, recorrer el PDF hasta `pág. 3/3`; pulsar **Marcar como completado**; esperar y recargar.
- **Esperado:** cambiar inmediatamente a **Ir al Examen** y persistir `contenido_visto`.
- **Evidencia:** `screenshots/iam-022-step-1.png`, `screenshots/iam-022-result.png`, `videos/iam-022-repro.webm`.
- **Nota:** IAM-007 sí queda verificado: en el mismo viewport bajo el PDF avanza de 1/3 a 3/3 y habilita el botón.

**Ticket existente que sigue reproduciéndose:** IAM-012. En el detalle del curso del estudiante, las tres clases sin `duration_seconds` siguen mostrando únicamente `s`; evidencia: `screenshots/iam-012-result.png`.

## Resumen

| Prioridad | Cantidad | Tickets |
|---|---|---|
| Crítico | 5 | IAM-004, 005, 006, 015, 016 |
| Alto | 3 | IAM-007, 008, 017 |
| Medio | 5 | IAM-009, 018, 019, 020, 021 |
| Bajo | 5 | IAM-010, 011, 012, 013, 014 |

---

## Lo que NO funciona

### Críticos

#### IAM-004 — Clase con examen activo y 0 preguntas bloquea al alumno
- **Falla:** `has_exam` es `true` por defecto en la API. Con 0 preguntas, `GET /topics/{id}/exam` responde 404 `No exam questions for this topic`. La UI no muestra error, la clase queda en `contenido_visto` para siempre, el curso nunca llega al 100% y no hay certificado.
- **Repro:** admin crea un tema sin preguntas con examen activo y publica el curso. El estudiante completa la clase anterior, abre esa y pulsa "Marcar como completado".
- **También desde la UI de admin:** guardar con "Requiere cuestionario" marcado y 0 preguntas no da error.
- **Fix:** bloquear `publish` si algún tema con examen tiene menos de 1 pregunta; `has_exam` por defecto `false`; mostrar el error en la UI.
- **Evidencia:** `screenshots/12-t2.png`

#### IAM-005 — El gating de completado lo afirma el cliente
- **Falla:** `POST /topics/{id}/heartbeat` acepta `last_page=99` con `total_pages=1` y toma `total_pages`, `pos_seconds`, `duration_seconds` y `max_seen_pct` del cliente. Con curl se completa PDF o video, se aprueba el examen y se emite el certificado en menos de 1 segundo.
- **Impacto:** el certificado deja de significar que el alumno vio el contenido.
- **Fix:** guardar `total_pages` en el servidor al guardar el bloque, rechazar `last_page > total_pages`, validar el avance contra el tiempo real entre heartbeats, usar solo `duration_seconds` del bloque.

#### IAM-006 — Límite de `/auth/sync` compartido por IP del proxy en producción
- **Falla:** slowapi usa `get_remote_address`; `infra/vps` corre uvicorn detrás de Caddy sin `--proxy-headers` ni `--forwarded-allow-ips`. Verificado en local: peticiones con distinto `X-Forwarded-For` comparten el mismo bucket.
- **Impacto:** en un registro masivo el 6.º alumno del minuto recibe 429 (límite 5 por minuto para todos).
- **Fix:** `--proxy-headers --forwarded-allow-ips` solo para la red interna de Docker, o limitar por `sub` del token.
- **Pendiente:** confirmarlo en el VPS real.

#### IAM-015 — Cada "Guardar" del tema borra el avance de todos los alumnos
- **Falla:** `handleSave` siempre llama a `PUT /topics/{id}/blocks`, que borra y recrea los bloques y su progreso y devuelve a `disponible` a todo alumno no aprobado, aunque solo cambie una errata en una pregunta.
- **Repro:** alumno con PDF 3 de 3 y estado `contenido_visto`; PUT con los mismos bloques → `pdf_last_page=0` y estado `disponible`.
- **Además:** el guardado son 3 llamadas no atómicas (tema, bloques, preguntas). Si la tercera falla, el progreso ya se perdió.
- **Fix:** no reenviar bloques sin cambios; upsert por `id` conservando progreso; endpoint transaccional.

#### IAM-016 — Guardar preguntas recrea todos los IDs y puede borrar el banco
- **Falla:** `POST /topics/{id}/questions/bulk` archiva todas las preguntas y crea nuevas; todos los IDs cambian en cada guardado.
  - Un alumno con examen abierto recibe `403 invalid_exam_token` al enviar y pierde sus respuestas.
  - El historial de intentos queda apuntando a preguntas archivadas.
  - Desmarcar "Requiere cuestionario" y guardar archiva todo el banco sin avisar.
  - `normalizeQuestion` marca en silencio la primera opción como correcta si la base de datos no tiene ninguna.
- **Fix:** upsert por `id` (como ya hace `PATCH /questions/{id}`), no archivar al desmarcar el examen, validar al menos 1 pregunta.

### Altos

#### IAM-007 — PDF requerido imposible de completar con ventana baja
- **Falla:** `ContentBlockPlayer.vue:202` usa `IntersectionObserver` con `threshold: 0.5` dentro de un contenedor `max-h-[80vh]`. Si la página (≈993 px) mide más del doble que el contenedor, nunca cuenta como vista. Ocurre con menos de ~620 px de alto: móvil horizontal, zoom 200%, ventanas pequeñas.
- **Repro:** viewport 1280×577 se queda en página 1/3; a 1280×900 llega a 3/3.
- **Fix:** umbral relativo al alto del contenedor.
- **Evidencia:** `screenshots/08-pdf-fin.png` y `09-pdf-ok.png`

#### IAM-008 — Dashboard admin muestra métricas inventadas
- **Falla:** `AdminDashboard.vue` (~línea 121) tiene datos fijos: "142 certificados", "+12 este mes", "María González obtuvo su certificado", rendimiento de módulos (120/85/43 activos), "Examen Final - Módulo 2: 65% reprueban". La base local tiene 1 a 3 estudiantes y 1 certificado.
- **Fix:** conectar a `/admin/dashboard` u ocultar las tarjetas sin datos reales.
- **Evidencia:** `screenshots/02-admin.png`

#### IAM-017 — `PATCH /admin/options/{id}` rompe "exactamente 1 correcta"
- **Falla:** marcar otra opción como correcta deja 2; desmarcar todas deja 0 (pregunta imposible de aprobar). Reproducido con 2 y con 0.
- **Nota:** la UI actual no usa este endpoint, pero está expuesto a admin e instructor.
- **Fix:** eliminar el endpoint o validar el invariante al final de la transacción.

### Medios

#### IAM-009 — `media_key` y subidas sin validación en servidor
- **Falla:** `PUT /admin/topics/{id}/blocks` acepta `media_key` inexistente, `pdf/../cover/x` y claves de 3000 caracteres. `POST /media/upload-url` valida solo el `content_type` declarado; no hay límite de tamaño ni verificación de magic bytes. Los "50 MB / 500 MB" son solo texto de la UI. Incumple el estándar de uploads.

#### IAM-018 — Enunciados con formato: el banco admin muestra HTML crudo
- **Falla:** `AdminPreguntas.vue:69` y `AdminModuloDetalle.vue:228` pintan `{{ enunciado }}`, así que se ve `<p>¿Pregunta <strong>0</strong>…</p>`. El estudiante lo ve bien.
- **También:** la ayuda del editor dice "5-300 caracteres" pero se permiten 5000; el mínimo cuenta etiquetas HTML (`<p>a</p>` pasa con 1 carácter real).
- **Fix:** renderizar con `sanitizeHtml`; validar longitud sobre texto sin HTML y unificar límites.
- **Evidencia:** `screenshots/14-admin-lista-preguntas.png`

#### IAM-019 — El editor genera formato que el sanitizador elimina
- **Falla:** `StarterKit` de Tiptap permite cita, código, tachado y línea horizontal (atajos de markdown como `> `). El allow-list solo conserva `p, br, strong, em, h2, h3, ul, ol, li, a`. El admin ve la cita o el código; el estudiante ve texto plano, y el editor también lo pierde al reabrir.
- **Fix:** restringir `StarterKit` a los nodos permitidos.
- **Evidencia:** `screenshots/15-texto-formato.png`

#### IAM-020 — Bloques de texto vacíos aceptados
- **Falla:** UI y API aceptan `<p></p>` y `<p><br></p>`. El estudiante ve una tarjeta vacía "TEXTO · Complementario".
- **Fix:** validar sobre texto plano (`editor.isEmpty` en la UI, quitar HTML en la API).

#### IAM-021 — Tras "Marcar como completado" no aparece "Ir al Examen"
- **Falla:** en una clase solo de texto, el servidor pasa a `contenido_visto` pero la pantalla sigue mostrando "Marcar como completado" hasta recargar.
- **Fix:** actualizar el estado local con la respuesta de `mark-content-done`.

### Bajos

| Ticket | Problema |
|---|---|
| IAM-010 | Sin `Authorization` responde 422 en vez de 401. El 429 de slowapi responde `{"error": "..."}` y no el contrato `{"error": {"code", "message"}}`. |
| IAM-011 | `POST /topics/{id}/questions` deja `order_index=0` en todas; el orden del examen no es determinista. |
| IAM-012 | El subtítulo de clase muestra `s · Con examen` cuando `duration_seconds` es null (`screenshots/07-leccion.png`). |
| IAM-013 | `GET /topics/{id}` devuelve el `media_key` de cada bloque al estudiante; sigue protegido por play-token pero CLAUDE.md pide ocultarlo. |
| IAM-014 | `seed_e2e.py` crea una clase sin bloques (viola "al menos 1 bloque") y usa `create_all`. |

---

## Lo que SÍ funciona

**Seguridad y aislamiento**
- Estudiante contra endpoints de admin (dashboard, estudiantes, cursos, reportes, subida): 403.
- Estudiante no inscrito: 403 en tema, examen, heartbeat y marcar completado.
- Clase bloqueada (la anterior no aprobada): 403 en tema, heartbeat, marcar completado, examen y play-token.
- Cursos en borrador: no aparecen en el catálogo, 404 por slug y no se pueden inscribir.
- Tokens de examen: `alg: none` rechazado; el token de otro alumno rechazado; un intento fallido exige repaso antes de reintentar.
- `/auth/sync` ignora `role` y `status` enviados en el cuerpo.
- Play-token solo con inscripción y clase desbloqueada.
- Gateway de media local (replica el worker): sin token 401, token con otra clave 403, Range 206.
- XSS: `<script>`, `<iframe>`, `<style>`, `onerror` y `javascript:` en texto de bloques y preguntas no se ejecutan en la vista del estudiante.
- Límite de 5 por minuto en `/auth/sync` funciona (con la salvedad de IAM-006).

**Flujos completos en pantalla**
- Login simulado, catálogo, inscripción.
- PDF con pdf.js en pantalla suficientemente alta: avanza 1/3 a 3/3 y aparece "Ir al Examen".
- Examen: preguntas con formato (negrita, cursiva, listas), opciones en orden aleatorio, resultado con aprobado o no, retroalimentación por pregunta.
- Subida directa desde el admin al bucket (URL firmada, preflight CORS y PUT).
- Guardado de tema desde el admin con confirmación.
- Verificación pública de certificado en `/verify/{uuid}`.
- Nombres con acentos, guiones y apóstrofes aceptados en el registro.

## Lo que falta por cubrir

- Reproducción de video real en `<video>` (requiere archivo de video), audio e imagen.
- Eliminar y archivar cursos, módulos y clases en admin; reportes y exportación; pantalla de estudiantes del admin.
- Diseño responsivo en móvil.
- Login real con Neon Auth (solo se probó el login simulado).
- Correos de Resend y descarga del PDF del certificado.
- Concurrencia de examen (doble envío).
- Examen diagnóstico a nivel de módulo.

## Notas del entorno de pruebas

- La base local quedó con datos de prueba (`QA Curso`, `Tema 3 formato`, usuarios s1 y s2) y una pregunta modificada durante las pruebas de IAM-017. Todo está en la base local; no afecta a producción.
- Archivos nuevos sin commitear: `compose.local.yaml`, `infra/local-media/`, cambios en `app/config.py`, `app/db.py`, `app/services/r2.py` y `alembic/env.py` (SSL y endpoint configurables).
