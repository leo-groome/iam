# Plan de Implementación: Activación Funcional del Panel de Administración (Frontend)

Este plan describe la estrategia para conectar el panel de administración del frontend (Vue.js) con los endpoints del backend (FastAPI), resolviendo las discrepancias de nomenclatura de variables, enrutamiento inconsistente, componentes mockeados y variables no declaradas.

## User Review Required

> [!IMPORTANT]
> **Estandarización de Parámetros (UUID vs Slug):** 
> Para evitar mezclas confusas entre slugs e IDs en el panel de administrador, este plan estandariza el uso de identificadores UUID (`:id`) en todas las rutas administrativas del router y en las llamadas API del frontend. El backend espera estrictamente UUIDs para las operaciones de edición/creación.
>
> **Consumo de Endpoints Protegidos:**
> Se sustituirá el uso de `/courses` públicos por `/api/v1/admin/courses` en las consultas de administrador. Esto garantiza que se validen los permisos del rol (`admin` o `instructor`) y que los instructores visualicen únicamente los cursos que les pertenecen (multitenancy).

## Open Questions

Ninguna pregunta abierta en este momento. Las discrepancias identificadas se alinean directamente con los esquemas de backend ya existentes.

---

## Proposed Changes

### Componente 1: Servicios API (`apps/frontend/src/services/`)

Consiste en crear un nuevo archivo de servicio que actúe como intermediario estructurado con la API del admin, exponiendo métodos fuertemente tipados.

#### [NEW] [admin.service.ts](file:///home/leo/Desktop/iam/apps/frontend/src/services/admin.service.ts)
* Crear `adminService` con llamadas a la API de administración utilizando `apiGet`, `apiPost`, `apiPatch` y `apiDelete` de `src/lib/api.ts`:
  * **Dashboard:** `getDashboardKpis()` -> `GET /api/v1/admin/dashboard`
  * **Cursos:**
    * `getCourses()` -> `GET /api/v1/admin/courses`
    * `getCourse(id)` -> `GET /api/v1/admin/courses/{id}`
    * `createCourse(data)` -> `POST /api/v1/admin/courses`
    * `updateCourse(id, data)` -> `PATCH /api/v1/admin/courses/{id}`
    * `publishCourse(id)` -> `POST /api/v1/admin/courses/{id}/publish`
    * `archiveCourse(id)` -> `POST /api/v1/admin/courses/{id}/archive`
    * `deleteCourse(id)` -> `DELETE /api/v1/admin/courses/{id}`
  * **Módulos:**
    * `createModule(courseId, data)` -> `POST /api/v1/admin/courses/{course_id}/modules`
    * `updateModule(id, data)` -> `PATCH /api/v1/admin/modules/{id}`
    * `deleteModule(id)` -> `DELETE /api/v1/admin/modules/{id}`
    * `reorderModules(courseId, order)` -> `POST /api/v1/admin/modules/reorder`
  * **Temas:**
    * `createTopic(moduleId, data)` -> `POST /api/v1/admin/modules/{module_id}/topics`
    * `updateTopic(id, data)` -> `PATCH /api/v1/admin/topics/{id}`
    * `deleteTopic(id)` -> `DELETE /api/v1/admin/topics/{id}`
    * `reorderTopics(moduleId, order)` -> `POST /api/v1/admin/topics/reorder`
  * **Preguntas:**
    * `createQuestion(topicId, data)` -> `POST /api/v1/admin/topics/{topic_id}/questions`
    * `updateQuestion(id, enunciado)` -> `PATCH /api/v1/admin/questions/{id}`
    * `archiveQuestion(id)` -> `DELETE /api/v1/admin/questions/{id}`
    * `updateOption(id, data)` -> `PATCH /api/v1/admin/options/{id}`
  * **Estudiantes:**
    * `getStudents(params)` -> `GET /api/v1/admin/students` (con filtros de búsqueda, estado y paginación)
    * `getStudentDetail(id)` -> `GET /api/v1/admin/students/{id}`
  * **Reportes:**
    * `getTopicPassRate(courseId)` -> `GET /api/v1/admin/reports/topic-pass-rate`
    * Generar URL para exportación de reportes CSV: `GET /api/v1/admin/reports/export?type={type}` (enrollments, completions, exam_attempts)

---

### Componente 2: Enrutamiento (`apps/frontend/src/router/`)

#### [MODIFY] [index.ts](file:///home/leo/Desktop/iam/apps/frontend/src/router/index.ts)
* Modificar las definiciones de rutas que requieran id/slug para que utilicen consistentemente el parámetro `:id` (UUID):
  * De `/admin/cursos/:id` a `/admin/cursos/:id` (asegurar uso estricto de ID).
  * Enrutadores internos de módulos, temas y preguntas:
    * `/admin/cursos/:id/modulos/:modId`
    * `/admin/cursos/:id/modulos/:modId/temas/:temaId`
    * `/admin/cursos/:id/modulos/:modId/temas/:temaId/preguntas`
    * `/admin/cursos/:id/modulos/:modId/temas/:temaId/preguntas/:qId`

---

### Componente 3: Vistas Administrativas (`apps/frontend/src/views/admin/`)

Se actualizará cada vista para consumir el nuevo `adminService`, usar variables mapeadas del backend (`modules`, `topics`, `content_type`, `has_exam`) y vincular formularios de forma reactiva.

#### [MODIFY] [AdminDashboard.vue](file:///home/leo/Desktop/iam/apps/frontend/src/views/admin/AdminDashboard.vue)
* Agregar bloque `<script setup>` con estado reactivo para almacenar las KPIs y cargar datos de `adminService.getDashboardKpis()` en `onMounted`.
* Reemplazar los valores estáticos por bindings de datos (`total_students`, `new_students_last_7d`, `active_courses`, `completion_rate`, `avg_exam_score`, `stuck_students`).
* Alimentar el gráfico de barra y lista de finalizaciones a partir de `enrollments_per_week` y `completions_per_course`.

#### [MODIFY] [AdminCursos.vue](file:///home/leo/Desktop/iam/apps/frontend/src/views/admin/AdminCursos.vue)
* Cambiar la llamada de carga a `adminService.getCourses()`.
* Corregir el enlace de edición de curso en la tabla para que apunte a `/admin/cursos/${c.id}` en lugar de usar slug.
* Actualizar la lectura de cantidad de módulos con `c.modules.length`.

#### [MODIFY] [AdminCursoDetalle.vue](file:///home/leo/Desktop/iam/apps/frontend/src/views/admin/AdminCursoDetalle.vue)
* Cambiar la lógica inicial para buscar `route.params.id` en lugar de `slug`.
* Si `isNew` es falso, cargar con `adminService.getCourse(id)`.
* Implementar variables reactivas y binding `v-model` para los inputs (Título, descripción corta/larga, restricciones de edad).
* Reemplazar `curso.modulos` por `curso.modules` y `m.temas` por `m.topics`.
* Añadir lógica a los botones "Guardar" y "Publicar/Archivar" para ejecutar `createCourse`/`updateCourse`/`publishCourse`/`archiveCourse`.

#### [MODIFY] [AdminModuloDetalle.vue](file:///home/leo/Desktop/iam/apps/frontend/src/views/admin/AdminModuloDetalle.vue)
* Corregir enrutamiento y extracción de parámetros a `route.params.id` y `route.params.modId`.
* Modificar iteraciones para usar `mod.topics` (inglés).
* Agregar reactividad a los campos y conectarlos con `adminService.createModule` / `adminService.updateModule`.

#### [MODIFY] [AdminTemaDetalle.vue](file:///home/leo/Desktop/iam/apps/frontend/src/views/admin/AdminTemaDetalle.vue)
* Corregir extracción de parámetros a `route.params.id`, `route.params.modId` y `route.params.temaId`.
* Reemplazar propiedades en español (`tema.type` -> `tema.content_type`, `tema.hasExam` -> `tema.has_exam`).
* Añadir bindings `v-model` e implementar lógica de guardado llamando a `adminService.createTopic` / `adminService.updateTopic`.

#### [MODIFY] [AdminPreguntas.vue](file:///home/leo/Desktop/iam/apps/frontend/src/views/admin/AdminPreguntas.vue)
* Reemplazar la sección `// TODO` para hacer fetch de las preguntas del tema y poblar la lista `questions`.
* Añadir lógica reactiva en el selector de `% mínimo para aprobar` (`exam_min_score`), guardando los cambios llamando a la API de actualización del tema al cambiar el valor.

#### [MODIFY] [AdminPreguntaDetalle.vue](file:///home/leo/Desktop/iam/apps/frontend/src/views/admin/AdminPreguntaDetalle.vue)
* Declarar las variables locales necesarias en el setup (`opts` array reactivo de strings para opciones, `correctIdx` número reactivo).
* Al editar, cargar el enunciado y las opciones recuperadas del backend.
* Implementar métodos reactivos para añadir opción, remover opción y guardar la pregunta (`adminService.createQuestion`/`updateQuestion`/`updateOption`).

#### [MODIFY] [AdminEstudiantes.vue](file:///home/leo/Desktop/iam/apps/frontend/src/views/admin/AdminEstudiantes.vue)
* Implementar tabla de estudiantes de forma dinámica conectada con `adminService.getStudents()`.
* Añadir buscador de texto y selector de estado (filtro) en el UI.
* Mostrar visualmente el estado del estudiante y la alerta especial de "stuck" si `student.is_stuck` es verdadero.
* Enlazar cada estudiante a su detalle: `/admin/estudiantes/${student.id}`.

#### [MODIFY] [AdminEstudianteDetalle.vue](file:///home/leo/Desktop/iam/apps/frontend/src/views/admin/AdminEstudianteDetalle.vue)
* Cargar detalles del alumno mediante `adminService.getStudentDetail(route.params.id)`.
* Mostrar información personal del alumno, tabla de cursos en los que se encuentra inscrito con su porcentaje de progreso y lista detallada de todos los intentos de exámenes (puntuación, fecha y resultado).

#### [MODIFY] [AdminReportes.vue](file:///home/leo/Desktop/iam/apps/frontend/src/views/admin/AdminReportes.vue)
* Implementar botones de exportación que abran o descarguen directamente desde la API:
  * Exportar Inscripciones -> `/api/v1/admin/reports/export?type=enrollments`
  * Exportar Finalizaciones -> `/api/v1/admin/reports/export?type=completions`
  * Exportar Intentos de Examen -> `/api/v1/admin/reports/export?type=exam_attempts`
* Mostrar listado de cursos para seleccionar y ver su respectiva tasa de aprobación por tema mediante `adminService.getTopicPassRate(courseId)`.

---

## Verification Plan

### Automated Tests
* Ejecutar chequeo estático y compilación de TypeScript para validar que no existan errores de tipado o variables no declaradas:
  ```bash
  pnpm build
  ```
* Ejecutar los tests E2E / unitarios del frontend si están definidos en:
  ```bash
  pnpm test
  ```

### Manual Verification
* Levantar el frontend y backend localmente.
* Iniciar sesión como usuario Administrador/Instructor.
* Navegar por las secciones:
  * Comprobar que el Dashboard carga datos numéricos y barras correspondientes a la BD real.
  * Crear, editar y eliminar un curso, módulo y tema piloto, verificando que los cambios persistan en el backend.
  * Cambiar el estado de un curso (publicar/archivar).
  * Modificar el banco de preguntas del examen y sus respectivas opciones de respuesta.
  * Visitar el listado de estudiantes, buscar por nombre, filtrar por estado y acceder a la ficha detallada de un alumno.
  * Descargar los reportes en CSV y constatar que se genera y recibe el stream correcto de datos.
