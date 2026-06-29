# PRD Frontend — Plataforma de Formación Paso a Paso

**Versión:** 2.3
**Fecha:** 2026-06-29
**Stack:** Vue 3 SPA + Vue Router + Pinia + Tailwind CSS + TypeScript (Vite)
**Alcance:** Definición completa de pantallas, reglas de negocio, patrones UX y límites del frontend.

---

## 1. Resumen del producto

Plataforma de formación digital "guiada de la mano". El público objetivo son personas con bajo nivel técnico, por lo que la experiencia debe ser lineal, autoexplicativa y libre de fricción. El backend es complejo; el frontend debe parecer trivial.

**Dos audiencias:**
- **Estudiante:** flujo ultra simplificado, una sola acción visible por pantalla.
- **Administrador:** panel completo para gestionar contenido, exámenes, estudiantes y métricas.

---

## 2. Stack técnico

| Capa | Tecnología | Justificación |
|---|---|---|
| Framework | **Vue 3 SPA** (Composition API + `<script setup>`) | SPA completa; toda la UI es interactiva. |
| Estilos | **Tailwind CSS** + variables CSS custom | Sistema de diseño rápido, consistente con theming via `--color-*`. |
| Tipado | **TypeScript** | Tipos generados desde OpenAPI en `src/lib/types.gen.ts`. |
| Estado cliente | **Pinia** | Stores: `auth`, `catalog`, `courses`, `progress`. |
| Routing | **Vue Router** (hash-less history) | Lazy imports en todas las rutas → code splitting automático. |
| Forms | **Zod** (validación manual en `<script setup>`) | Validación tipada sin librería de forms. |
| Auth | **@stackframe/js** (Neon Auth) | JWT validado en backend; `useAuthStore` expone `user` reactivo. |
| HTTP | `apiFetch` / `apiGet` / `apiPost` en `src/lib/api.ts` | Añade `Authorization: Bearer` automáticamente. |
| Player video | `<video>` nativo + HTTP Range Requests (Worker R2) | Streaming nativo, sin seek hacia adelante. |
| Visor PDF | `<iframe>` con Blob URL (fetch privado) | Archivos privados sin exponer URL firmada en DOM. |
| Storage media | Cloudflare R2 + Worker (play-token JWT) | Upload directo desde browser; streaming autenticado. |
| Build | **Vite** + `manualChunks` (vendor-vue / vendor-ffmpeg / vendor) | Chunks separados para caching óptimo. |
| Deploy | **Vercel** (CI/CD vía GitHub push a `main`) | — |

**Convenciones de proyecto:**
- Carpetas: `src/views/`, `src/components/ui/`, `src/layouts/`, `src/stores/`, `src/services/`, `src/lib/`.
- Vistas separadas por audiencia: `views/admin/`, `views/student/`, `views/public/`.
- Servicios por audiencia: `courses.service.ts` (estudiante) y `admin.service.ts` (admin).
- IDs en rutas admin: **UUID**. Rutas de estudiante: **slug** / `topicId` (UUID).
- Convención de nombres: PascalCase para componentes, camelCase para composables/servicios.

---

## 3. Decisiones de producto consolidadas

| Tema | Decisión |
|---|---|
| Estructura de contenido | Curso → Módulos → Temas |
| Tipos de contenido por tema | Video, PDF, infografía/imagen, texto enriquecido |
| Control de video | Obligatorio ver completo (sin adelantar) |
| Examen | Opción múltiple, preguntas aleatorizadas |
| Falla en examen | Repaso forzoso (regresa al video del tema) |
| Fecha límite | Sin límite — ritmo libre |
| Certificado | PDF descargable al completar 100% del curso |
| Autenticación | Google + email/password |
| Onboarding | Deck de tarjetas antes del registro; datos pre-rellenan nombre en signup. |
| Restricción por edad | **Eliminada.** `age_min`/`age_max` existen en DB pero no se filtran. Todos los cursos publicados son visibles para todos los usuarios autenticados. |
| Estética | Corporativo limpio (azul/blanco, profesional, minimalista) |
| Dispositivos | Responsive completo (móvil y desktop por igual) |
| Idioma | Español |
| Reporte admin | Correo semanal con resumen de finalizaciones |

---

## 4. Reglas de negocio (frontend)

### 4.1 Reglas de acceso y registro
- **R-AUTH-01:** Todo estudiante debe autenticarse antes de acceder a cualquier contenido.
- **R-AUTH-02:** El registro requiere obligatoriamente: nombre, correo, contraseña (o cuenta Google), fecha de nacimiento.
- **R-AUTH-03:** La edad se calcula desde la fecha de nacimiento; nunca se pide la edad directamente.
- **R-AUTH-04:** Edad mínima permitida para registrarse: **13 años**. Menor → bloqueo con mensaje "No cumples la edad mínima para usar la plataforma".
- **R-AUTH-05:** El correo debe ser único. Duplicado → "Ya existe una cuenta con este correo. ¿Quieres iniciar sesión?".
- **R-AUTH-06:** Contraseña: mínimo 8 caracteres, al menos 1 número. No se pide símbolos ni mayúsculas obligatorias (evitar fricción).
- **R-AUTH-07:** Sesión persistente por 30 días. Refresh silencioso al detectar expiración.
- **R-AUTH-08:** Logout limpia sesión y redirige a Landing.

### 4.2 Reglas de catálogo y elegibilidad
- **R-CAT-01:** El catálogo muestra **todos** los cursos publicados sin filtro de edad.
- **R-CAT-02:** Cursos en estado `borrador` no aparecen jamás al estudiante.
- **R-CAT-03:** Cursos `archivados` no aparecen, pero estudiantes ya inscritos pueden completarlos.
- **R-CAT-04:** El catálogo se divide en secciones: "Continuar donde lo dejé" (progress > 0 < 100), "Cursos disponibles" (sin iniciar), "Ya completados" (100%).
- **R-CAT-05:** Si no hay cursos → estado vacío con mensaje apropiado.
- **R-CAT-06:** El catálogo usa `useCatalogStore` — segunda visita muestra cache inmediatamente mientras refetch corre en background.

### 4.3 Reglas de progreso
- **R-PROG-01:** Un curso solo inicia cuando el estudiante presiona "Empezar curso". Sin auto-inicio.
- **R-PROG-02:** Los temas se desbloquean **secuencialmente**. No se puede saltar al tema 3 sin completar 1 y 2.
- **R-PROG-03:** Un tema se considera completado cuando:
  - Contenido visto al 100%, **y**
  - Examen aprobado (si el tema lo requiere).
- **R-PROG-04:** El progreso del curso es: `(temas completados / total temas) * 100`, redondeado a entero.
- **R-PROG-05:** El estudiante puede salir en cualquier momento; al volver, retoma exactamente en el tema actual.
- **R-PROG-06:** No se permite "abandonar" cursos manualmente en v1.

### 4.4 Reglas de consumo de contenido
- **R-VID-01:** El reproductor de video **no permite seek hacia adelante**. Solo play, pause, volumen y seek hacia atrás (re-ver).
- **R-VID-02:** Se considera video "visto" al alcanzar el 95% del tiempo total (tolerancia para créditos finales).
- **R-VID-03:** Si el usuario cierra/refresca durante el video, se guarda el último timestamp visto y reanuda desde ahí.
- **R-VID-04:** El botón de examen aparece **únicamente** cuando el video llega al 95%.
- **R-PDF-01:** Un PDF se considera leído cuando el usuario llega a la última página (scroll/navegación).
- **R-PDF-02:** El botón de examen aparece al marcar última página visitada.
- **R-IMG-01:** Imagen/infografía: tras 5 segundos de visualización y scroll completo → habilita continuar.
- **R-TXT-01:** Texto enriquecido: scroll al 90% del contenido habilita continuar.

### 4.5 Reglas de examen
- **R-EX-01:** Solo se accede al examen tras completar el contenido del tema.
- **R-EX-02:** Preguntas se presentan en **orden aleatorio** por intento.
- **R-EX-03:** Opciones de respuesta también se aleatorizan por pregunta.
- **R-EX-04:** Una pregunta a la vez. No se puede regresar a preguntas previas.
- **R-EX-05:** No hay temporizador en v1.
- **R-EX-06:** Calificación = (correctas / total) * 100.
- **R-EX-07:** Aprueba si calificación ≥ `% mínimo` definido por admin para ese tema.
- **R-EX-08:** Reprobado → **repaso forzoso**: redirige al contenido del tema y debe re-completarlo (100% otra vez) antes de re-intentar.
- **R-EX-09:** No hay límite de intentos en v1.
- **R-EX-10:** No se muestra qué pregunta falló al reprobar (refuerza repaso completo). Solo calificación obtenida y mínima requerida.
- **R-EX-11:** Al aprobar se muestra solo calificación + felicitación. Sin desglose de respuestas.

### 4.6 Reglas de certificado
- **R-CERT-01:** Se genera al alcanzar 100% del curso.
- **R-CERT-02:** Contenido: nombre completo del estudiante, nombre del curso, fecha de finalización, ID único.
- **R-CERT-03:** Formato PDF, tamaño carta horizontal, descargable infinitas veces desde el perfil.
- **R-CERT-04:** Si el nombre del estudiante cambia, el certificado refleja el nombre **al momento de descarga**.

### 4.7 Reglas de panel admin
- **R-ADM-01:** Solo usuarios con rol `admin` pueden acceder a `/admin/*`.
- **R-ADM-02:** No se puede eliminar un curso con estudiantes inscritos. Solo archivar.
- **R-ADM-03:** No se puede eliminar un tema si tiene progreso de estudiantes. Solo editar contenido.
- **R-ADM-04:** Las preguntas se pueden editar, pero los intentos previos del estudiante mantienen su calificación histórica.
- **R-ADM-05:** Cambiar el % mínimo de aprobación afecta **solo a intentos futuros**.
- **R-ADM-06:** El admin puede ver detalle de cualquier estudiante pero **no impersonarlo** en v1.
- **R-ADM-07:** El correo semanal se envía los lunes 9:00 AM hora local del admin (configurable en v2).

---

## 5. Límites técnicos y validaciones

### 5.1 Límites de contenido (admin)

| Campo | Tipo | Mínimo | Máximo | Notas |
|---|---|---|---|---|
| Título de curso | texto | 5 | 80 caracteres | |
| Descripción corta curso | texto | 10 | 160 caracteres | Para tarjeta del catálogo |
| Descripción larga curso | texto | 0 | 2 000 caracteres | Markdown soportado |
| Imagen de portada curso | imagen | — | 2 MB | JPG/PNG/WebP, ratio 16:9, mín 1280×720 |
| Edad mínima curso | número | 13 | 99 | |
| Edad máxima curso | número | 13 | 99 | Debe ser ≥ edad mínima |
| Módulos por curso | conteo | 1 | 30 | |
| Título de módulo | texto | 3 | 60 caracteres | |
| Temas por módulo | conteo | 1 | 50 | |
| Título de tema | texto | 3 | 60 caracteres | |
| Video (archivo) | mp4/webm | — | 500 MB | Recomendado <100 MB |
| Video (duración) | tiempo | 10 seg | 90 min | |
| PDF | pdf | — | 50 MB | Máx 200 páginas |
| Imagen/infografía | imagen | — | 5 MB | JPG/PNG/WebP/SVG |
| Texto enriquecido | texto | 100 | 20 000 caracteres | |
| Preguntas por tema | conteo | 1 | 30 | |
| Enunciado de pregunta | texto | 5 | 300 caracteres | |
| Opciones por pregunta | conteo | 3 | 5 | |
| Texto por opción | texto | 1 | 150 caracteres | |
| % mínimo aprobación | número | 50 | 100 | Default 70 |

### 5.2 Límites de usuario (estudiante)

| Campo | Mínimo | Máximo | Notas |
|---|---|---|---|
| Nombre completo | 3 | 80 caracteres | Solo letras, espacios, acentos |
| Correo | — | 120 caracteres | Formato RFC 5322 |
| Contraseña | 8 | 64 caracteres | ≥1 número |
| Fecha de nacimiento | — | — | Edad calculada 13-120 |

### 5.3 Límites operativos

- **Paginación admin (tablas):** 25 filas por página, máx 100.
- **Búsqueda admin:** mínimo 2 caracteres, debounce 300 ms.
- **Catálogo estudiante:** carga inicial 12 cursos, scroll infinito de 12 en 12.
- **Tiempo máximo de sesión inactiva:** 24 h en estudiante, 2 h en admin (re-login).
- **Subida de archivos:** progreso visible, cancelable. Timeout 10 min.
- **Rate limit visual:** botón de envío se deshabilita durante peticiones para evitar doble click.

### 5.4 Performance budgets

| Métrica | Objetivo |
|---|---|
| Lighthouse Performance (móvil) | ≥ 90 |
| LCP (móvil 4G) | < 2.5 s |
| CLS | < 0.1 |
| INP | < 200 ms |
| Bundle JS por ruta de estudiante | < 150 KB gzip |
| Bundle JS panel admin | < 400 KB gzip |
| Imágenes | `loading="lazy"` en todas; covers con fade-in desde placeholder |
| Chunks Vite | vendor-vue / vendor-ffmpeg / vendor separados para caching |
| Navegación entre rutas | Progress bar de página visible en ≤ 50 ms post-click |

### 5.5 Accesibilidad (WCAG 2.1 AA)

- Contraste mínimo 4.5:1 en texto normal, 3:1 en texto grande.
- Todo elemento interactivo accesible por teclado (Tab, Enter, Esc).
- Foco visible (outline 2px azul).
- Imágenes con `alt` obligatorio en admin.
- Labels asociados a inputs (`<label for>`).
- Anuncios de cambios de estado con `aria-live` (resultado de examen, progreso).
- Tamaño táctil mínimo 44×44 px en móvil.

### 5.6 Compatibilidad

- **Navegadores:** últimas 2 versiones de Chrome, Edge, Firefox, Safari. Safari iOS 15+.
- **Resoluciones:** 320 px a 2560 px de ancho.
- **No soporte:** Internet Explorer.

---

## 6. Estados y transiciones

### 6.1 Estado del estudiante
- `nuevo` → primera vez, sin cursos iniciados.
- `activo` → al menos un curso en progreso.
- `completado` → al menos un curso finalizado.
- `atorado` → reprobó el mismo examen 3+ veces (señal visible al admin).

### 6.2 Estado del curso (por estudiante)
- `no_iniciado` → no presionó "Empezar".
- `en_progreso` → 1-99% completado.
- `completado` → 100%.

### 6.3 Estado del tema (por estudiante)
- `bloqueado` → temas anteriores no completados.
- `disponible` → tema actual desbloqueado.
- `contenido_visto` → consumió contenido, pendiente examen.
- `aprobado` → tema cerrado.
- `en_repaso` → reprobó, debe re-ver contenido.

### 6.4 Estado del curso (admin)
- `borrador` → editable, no visible al estudiante.
- `publicado` → visible y accesible.
- `archivado` → oculto a nuevos, accesible a inscritos.

---

## 7. Principios de diseño (estudiante)

1. **Una acción primaria por pantalla.** Un solo botón grande visible.
2. **Sin menús anidados.** Navegación lineal; la app dice qué sigue.
3. **Estado siempre visible.** Barra de progreso del curso en todo momento.
4. **Errores en lenguaje humano.** Nunca códigos ni jerga técnica.
5. **Refuerzo positivo.** Confirmaciones visuales al completar cada paso.
6. **Tipografía amplia, contraste alto, botones grandes.** Accesibilidad para usuarios mayores o con baja experiencia digital.
7. **Sin sorpresas.** Toda acción destructiva pide confirmación.

---

## 8. Mapa de pantallas — ESTUDIANTE

### 8.1 Landing / Login (`/`)
- Logo + nombre plataforma + tagline.
- Botón grande "Entrar con Google".
- Link secundario "Entrar con correo y contraseña" → expande campos.
- Link "Crear cuenta nueva" → `/registro`.

### 8.2 Registro (`/registro`)
- Campos: nombre, correo, contraseña, fecha nacimiento.
- Botón Google alternativo.
- Aceptación de términos (checkbox obligatorio).
- Botón "Crear mi cuenta".
- Validación cliente con Zod en tiempo real.

### 8.3 Catálogo (`/catalogo`)
- Saludo "Hola, [nombre]".
- Sección "Continuar donde lo dejé" (si aplica).
- Grid de cursos filtrados por edad.
- Cada tarjeta: portada, título, descripción corta, duración, botón "Comenzar" o "Continuar".
- Estado vacío si no hay elegibles.

### 8.4 Detalle del curso (`/curso/[id]`)
- Portada + título + descripción larga.
- Lista de módulos (colapsable) con temas.
- Barra de progreso.
- Botón "Empezar curso" o "Continuar".

### 8.5 Pantalla de aprendizaje (`/curso/[id]/tema/[temaId]`)
**Pantalla núcleo.**
- Header mínimo: nombre curso + barra progreso global + botón salir.
- Sidebar colapsable con módulos/temas (estado bloqueado/actual/completado).
- Área central según tipo de contenido:
  - **Video:** player sin seek adelante. Tracking de % visto.
  - **PDF:** visor con páginas leídas.
  - **Imagen:** vista full-width + zoom.
  - **Texto:** lectura tipo artículo.
- Botón único inferior, cambia según estado.

### 8.6 Pantalla de examen (`/curso/[id]/tema/[temaId]/examen`)
- "Cuestionario del tema: [nombre]".
- Una pregunta a la vez.
- "Pregunta X de Y" + indicador visual.
- Botón "Siguiente" / "Enviar respuestas".
- Confirmación antes de enviar el último.

### 8.7 Resultado del examen
- **Aprobado:** calificación + mensaje + botón "Continuar al siguiente tema".
- **Reprobado:** calificación + mínima requerida + mensaje empático + botón "Volver a ver el video".

### 8.8 Repaso forzoso
- Misma pantalla de aprendizaje con banner "Repaso del tema".
- Al completar nuevamente → habilita reintento.

### 8.9 Progreso panorámico (modal o `/curso/[id]/progreso`)
- Lista de módulos con estado.
- Porcentaje total + tiempo invertido estimado.
- Botón "Continuar" al tema actual.

### 8.10 Certificado (`/curso/[id]/certificado`)
- Animación de celebración.
- Vista previa del certificado.
- Botón "Descargar mi certificado".
- Botón secundario "Ver otros cursos".

### 8.11 Mi perfil (`/perfil`)
- Datos básicos.
- Lista de certificados obtenidos.
- Cerrar sesión.

### 8.12 Estados vacío/error
- Sin cursos disponibles.
- Sin conexión.
- Sesión expirada.
- 404.

---

## 9. Mapa de pantallas — ADMINISTRADOR

### 9.1 Login admin (`/admin/login`)
- Email + password. Sin Google.

### 9.2 Dashboard (`/admin`)
- KPIs: estudiantes (total + últimos 7 días), cursos activos, tasa finalización, promedio calificaciones.
- Gráficas: inscripciones por semana, finalizaciones por curso, distribución calificaciones.
- Alertas: estudiantes atorados.

### 9.3 Lista de cursos (`/admin/cursos`)
- Tabla con columnas, filtros, búsqueda.
- Botón "Crear curso nuevo".
- Acciones: editar, duplicar, archivar.

### 9.4 Editor de curso (`/admin/cursos/[id]`)
- Datos generales + restricción edad + estado.
- Sub-sección módulos drag&drop.

### 9.5 Editor de módulo (`/admin/cursos/[id]/modulo/[modId]`)
- Datos + lista de temas drag&drop.

### 9.6 Editor de tema (`/admin/cursos/[id]/modulo/[modId]/tema/[temaId]`)
- Título + tipo + upload/editor + toggle examen.

### 9.7 Banco de preguntas (`/admin/.../tema/[temaId]/preguntas`)
- Lista + % mínimo + botón "Agregar pregunta".

### 9.8 Editor de pregunta (modal)
- Enunciado + 3-5 opciones + correcta + guardar.

### 9.9 Lista de estudiantes (`/admin/estudiantes`)
- Tabla con filtros, búsqueda, alertas de atorados.

### 9.10 Detalle de estudiante (`/admin/estudiantes/[id]`)
- Perfil + cursos con progreso + calificaciones por examen.

### 9.11 Reportes (`/admin/reportes`)
- Exportar CSV/Excel.
- Tasa de aprobación por tema.

### 9.12 Configuración (`/admin/configuracion`)
- Toggle correo semanal + destino.
- Branding básico.
- Términos y privacidad.

---

## 10. Componentes UI reutilizables

### Player y contenido
- **`LearningPlayer.vue`** — video (HTTP Range, buffering overlay, progress bar CTA), PDF (iframe Blob), imagen, texto. Emite `content-done` al completar.
- **`ExamRunner.vue`** — pregunta por pregunta, aleatorizado.

### Carga y feedback visual
- **`SkeletonCard.vue`** — props: `hasImage`, `hasIcon`, `hasSubtitle`, `hasFooter`. Animate-pulse.
- **`SkeletonStats.vue`** — KPI placeholder para dashboard admin.
- **`SkeletonTable.vue`** — props: `rows`, `columns`, `hasAvatar`. Para tablas admin.
- **`SkeletonText.vue`** — props: `lines`, `hasTitle`, `titleWidth`. Para bloques de texto.
- **`PageProgressBar.vue`** — barra de 2px en top del viewport, activa en cada navegación de ruta via `router.beforeEach/afterEach`. Sin dependencias externas.
- **`ProgressBar.vue`** — barra de progreso lineal con porcentaje. Lee de `useProgressStore` en CourseDashboard.

### Navegación y layout
- **`CourseCard.vue`** — tarjeta del catálogo con cover, título, descripción y progreso.
- **`AuthSplit.vue`** — layout split para login/signup con validación Zod.
- **`PageHeader.vue`**, **`GreetingHeader.vue`**, **`Banner.vue`**, **`StatCard.vue`**, **`EmptyState.vue`**.

### Layouts
- **`PublicLayout.vue`** — landing, login, signup, onboarding.
- **`StudentLayout.vue`** — catálogo, curso, lección. Navbar con progreso.
- **`AdminLayout.vue`** — sidebar, header, contenido.

### Stores
- **`auth`** — user, isAuthenticated, isAdmin, init/login/logout.
- **`catalog`** — courses[], loading, refetch(), getBySlug(). Cache entre navegaciones.
- **`progress`** — progressByCourse{}, hydrate(slug, data), updateProgress(slug, pct). Actualización optimista post mark-content-done.
- **`courses`** — reservado (no usado activamente aún).

---

## 10.5 Patrones UX de carga (Optimistic UI)

### Regla general
Toda escritura al servidor sigue el patrón: **actualizar UI inmediatamente → llamar API → rollback si falla**.

### Patrones implementados

| Situación | Patrón |
|---|---|
| Enrollment en curso | Navegar inmediatamente; `enroll()` en background. Si falla, LessonView reintenta en `onMounted`. |
| `mark-content-done` | Spinner "Registrando progreso..." mientras vuela la request. Al éxito: CTA se desbloquea con spring transition + checkmark 2s. |
| Progreso del curso | `progressStore.updateProgress(slug, pct)` calculado localmente al `content-done`. CourseDashboard lo lee reactivo sin refetch. |
| Buffering de video | Spinner overlay `bg-black/50` activo en `waiting`/`stalled`, oculto en `canplay`/`playing`. |
| Progreso hacia desbloqueo | Barra fina sobre el CTA que crece con `videoProgress` hacia el umbral de 95%. |
| Catálogo (segunda visita) | Muestra cache inmediatamente, refetch silencioso en background via `catalogStore.refetch()`. |
| Cover de curso | Placeholder `animate-pulse` hasta `@load`; imagen hace fade-in en 500ms. |
| Navegación entre rutas | `PageProgressBar` arranca en `beforeEach` (exponential approach a 88%), completa en `afterEach`. |
| Título de tema | Skeleton sincronizado con el player durante `loadingTema` — revelan juntos. |

### Skeleton pattern uniforme
Todas las vistas con datos remotos usan:
```html
<transition name="fade" mode="out-in">
  <SkeletonXxx v-if="loading" />
  <div v-else class="animate-fade-in"><!-- contenido real --></div>
</transition>
```

---

## 11. Sistema visual

- **Paleta (referencia visual aprobada):**
  - Azul primario: `#1448E0` (botones, headings de acento, CTAs)
  - Azul primario hover: `#0F3BBF`
  - Azul claro fondo: `#EEF2FF` (fondo general de la app)
  - Azul muy claro chip: `#DCE6FF` (badges, círculos de ícono, tags tipo "12 min")
  - Blanco: `#FFFFFF` (tarjetas, contenedores)
  - Borde sutil: `#E5EAF5`
  - Texto principal: `#0B1220` (casi negro, alto contraste)
  - Texto secundario: `#5B6573` (descripciones, metadatos)
  - Éxito: `#10B981`
  - Error: `#EF4444`
  - Advertencia: `#F59E0B`
- **Tipografía:** Inter (sistema fallback `system-ui`). Base 16 px móvil, 18 px desktop.
- **Espaciado:** escala Tailwind (4-base). Padding generoso (mín 16 px en contenedores).
- **Bordes:** radio 8 px componentes, 12 px tarjetas, 16 px modales.
- **Sombras:** sutiles, `shadow-sm` en tarjetas, `shadow-lg` en modales.
- **Iconos:** Lucide, 20-24 px.
- **Modo claro únicamente** en v1.

---

## 12. Flujos críticos

**Estudiante (camino feliz):**
Login → Catálogo → Detalle curso → Empezar → Video tema 1 → 95% visto → Botón examen → Aprueba → Siguiente tema → … → 100% curso → Descarga certificado.

**Estudiante (reprobado):**
Examen → Reprobado → Repaso forzoso → Ver video 100% otra vez → Botón examen → Reintento → Aprueba.

**Admin (crear curso completo):**
Login admin → Crear curso (datos + edad) → Agregar módulo → Agregar tema (subir video) → Crear preguntas + % aprobación → Repetir → Publicar.

**Admin (monitorear atorado):**
Dashboard → Alerta "X estudiantes atorados" → Lista estudiantes filtrada → Detalle estudiante → Ver tema y exámenes fallidos.

---

## 13. Mensajes y microcopy clave

| Situación | Mensaje |
|---|---|
| Bienvenida | "Hola, [nombre]. ¿Listo para aprender?" |
| Empezar curso | "Empezar curso" |
| Continuar | "Continuar donde lo dejé" |
| Habilitar examen | "Hacer cuestionario" |
| Aprobado | "¡Aprobado! Sacaste [X]." |
| Reprobado | "No esta vez. Vamos a repasar juntos." |
| Curso completado | "¡Felicidades! Terminaste el curso." |
| Sin cursos | "No hay cursos disponibles para tu perfil en este momento." |
| Sin conexión | "Parece que perdiste conexión. Reintentando..." |
| Error genérico | "Algo no salió bien. Intenta de nuevo en un momento." |
| Confirmar salir examen | "Si sales ahora, perderás tus respuestas. ¿Seguro?" |

---

## 14. Fuera de alcance (v1)

- App nativa móvil (solo web responsive).
- Pagos / cursos de pago.
- Foros / comentarios entre estudiantes.
- Chat con instructor.
- Multi-idioma.
- Modo oscuro.
- Gamificación.
- Impersonación de estudiantes desde admin.
- Modo offline.
- Notificaciones push.

---

## 15. Checklist final de pantallas

**Estudiante (12):** Landing/Login · Registro · Catálogo · Detalle curso · Aprendizaje · Examen · Resultado · Repaso forzoso · Progreso · Certificado · Perfil · Estados vacío/error.

**Admin (12):** Login · Dashboard · Lista cursos · Editor curso · Editor módulo · Editor tema · Banco preguntas · Editor pregunta · Lista estudiantes · Detalle estudiante · Reportes · Configuración.

**Total: 24 pantallas.**

---

## 16. Criterios de aceptación globales

- [ ] Toda pantalla responsive 320 px → 2560 px.
- [ ] Toda interacción accesible por teclado.
- [ ] Lighthouse Performance ≥ 90 en móvil para rutas de estudiante.
- [ ] Todos los formularios validan con Zod cliente + muestran errores claros.
- [ ] Estados de carga (skeleton) en cada vista que dependa de datos remotos.
- [ ] Cero textos en inglés en la UI de estudiante.
- [ ] Todas las reglas de la sección 4 implementadas y verificables.
- [ ] Límites de la sección 5 respetados en formularios admin.
