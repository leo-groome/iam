# Reporte de Auditoría Técnica — Panel de Administración (IAM)

Este documento detalla los hallazgos de la auditoría técnica realizada sobre el panel de administración (`/admin`) en el frontend (Vue.js) y su integración con el backend (FastAPI), identificando ineficiencias de flujo, fallas en los endpoints y una propuesta de rediseño para el módulo de exámenes.

---

## 1. Auditoría del Flujo Académico (Cursos → Módulos → Clases)

El flujo jerárquico actual del contenido está estructurado de la siguiente manera:
1. **Cursos:** `/admin/cursos/:id` (Edición general del curso y vista del árbol de módulos y clases).
2. **Módulos:** `/admin/cursos/:id/modulos/:modId` (Detalle del módulo y clases que lo componen).
3. **Clases (Temas):** `/admin/cursos/:id/modulos/:modId/temas/:temaId` (Detalle de contenido, tipo y toggle de examen).

### Hallazgos Críticos de Navegación y Renderizado
> [!WARNING]
> **Bug de Doble `<router-view>` en Layouts**
> Se identificó un error estructural en los layouts (`AdminLayout.vue`, `StudentLayout.vue`, `PublicLayout.vue`). Estos archivos heredan y renderizan `<router-view />` internamente en lugar de utilizar `<slot />`, a pesar de que `App.vue` los monta dinámicamente envolviendo otro `<router-view />`. Esto provoca problemas de ciclo de vida en el enrutador y retrasos de renderizado al cargar vistas administrativas.

> [!IMPORTANT]
> **Flujo Ineficiente de Cuestionarios**
> Para configurar o modificar un examen actualmente se requiere:
> 1. Activar el toggle "Requiere cuestionario" en el detalle del tema (`AdminTemaDetalle.vue`).
> 2. Hacer clic en "Editar banco de preguntas", lo que redirige a una lista de preguntas (`AdminPreguntas.vue`).
> 3. Hacer clic en "Editar" o "+ Agregar pregunta", redirigiendo a una pantalla individual (`AdminPreguntaDetalle.vue`).
> 4. Guardar y regresar a la lista, repitiendo el proceso para cada pregunta individual.
>
> Este flujo incrementa la fricción (más de 50 clics/navegaciones para un examen de 10 preguntas) y es extremadamente lento debido a la fragmentación de la UI.

---

## 2. Rediseño del Creador de Exámenes (Concepto "Google Forms")

Para simplificar la creación y edición de exámenes, proponemos consolidar todo el flujo de preguntas y opciones en **una sola pantalla dinámica**, integrada directamente en la vista del tema o módulo.

### Diseño Propuesto (UX/UI)
- **Vista Unificada:** Al activar "Requiere cuestionario", se despliega un contenedor dinámico abajo. No hay redirecciones de página.
- **Tarjetas de Pregunta In-Place:** Cada pregunta se renderiza como una tarjeta editable:
  - Input de texto para el enunciado (con validación de longitud).
  - Listado de 3 a 5 opciones con campos de texto directamente editables.
  - Selector tipo radio al lado de cada opción para definir cuál es la respuesta correcta de forma inmediata.
  - Botones directos para "Agregar opción", "Eliminar opción" y "Eliminar pregunta".
  - Drag and drop (mediante `vuedraggable` o similar) para reordenar las preguntas en el cuestionario.

### Propuesta Técnica en el Backend (Endpoint Bulk)
Actualmente, el backend requiere llamadas individuales para crear cada pregunta y modificar cada opción (`PATCH /api/v1/admin/options/{id}`). Esto generaría docenas de peticiones HTTP en una sola pantalla.

> [!TIP]
> **Endpoint de Guardado Masivo (Recomendado)**
> Se propone implementar un nuevo endpoint en el backend para realizar la operación de forma atómica:
> - **Ruta:** `POST /api/v1/admin/topics/{topic_id}/questions/bulk`
> - **Payload:** Un array completo de preguntas y opciones.
> - **Lógica:** El backend limpia las preguntas previas del examen (respetando registros históricos de intentos) y escribe el nuevo set en una sola transacción SQL.

---

## 3. Auditoría de Endpoints Desconectados o Incorrectos

Durante la auditoría del tráfico de red y el comportamiento del backend, se detectaron múltiples discrepancias graves de integración y endpoints simulados:

### A. Fallas de Autenticación en Descarga de Reportes (CSV)
- **Ruta:** `/api/v1/admin/reports/export?type={type}`
- **Problema:** El frontend invoca la descarga mediante `window.open(..., '_blank')`. Al abrir una pestaña nueva, el navegador **no envía** el header `Authorization: Bearer <token>`, resultando en un error `401 Unauthorized` inmediato.
- **Solución:** Consumir el endpoint mediante `apiFetch` (que incluye el token JWT), recibir el stream como `Blob` y forzar la descarga en el cliente mediante una URL de objeto temporal.

### B. Mapeo Incorrecto de Atributos en Detalles de Estudiante
- **Ruta:** `GET /api/v1/admin/students/{id}`
- **Falla en Inscripciones (Enrollments):** El backend devuelve el progreso en `progress_cached`. Sin embargo, el frontend (`AdminEstudianteDetalle.vue`) busca `progress_percentage`. Esto ocasiona que el progreso de todos los alumnos se muestre en **0%**.
- **Falla en Intentos (Attempts):** El frontend intenta renderizar `a.topic_title`, pero el esquema del backend (`ExamAttemptSummary`) únicamente expone `topic_id`. Esto causa que la columna de "Tema" se muestre **completamente vacía**.
- **Falta de Estado:** El frontend lee `e.status`, pero la inscripción devuelta por el backend no contiene dicho campo.

### C. Mismatch en Búsqueda del Directorio de Estudiantes
- **Ruta:** `GET /api/v1/admin/students`
- **Problema:** El frontend envía el parámetro de búsqueda como `search` (`{ query: { search: ... } }`). Sin embargo, el backend FastAPI espera estrictamente el parámetro `q` (`q: str | None = Query(None)`). Debido a esto, la búsqueda de estudiantes **no aplica ningún filtro** y siempre devuelve el listado completo.

### D. Componentes 100% Mockeados / Falsos en Frontend
- **Editor de Landing Page (`/admin/landing/*`):** Las secciones (Inicio, Pilares, Quiénes somos, Ecos) son plantillas de HTML estático. No guardan datos reactivos, no tienen lógica de guardado y no están conectadas a ninguna tabla o endpoint del backend.
- **Configuración del Sistema (`/admin/configuracion`):** Los campos están guardados localmente en memoria. El botón "Guardar cambios" solo simula un spinner usando un delay de `setTimeout` de 800ms. No existe un router de configuración (`/api/v1/config`) en FastAPI.

### E. Bug de Filtro de Edad en Catálogo (Backend)
- **Problema:** En el backend, la función de consulta `get_courses_for_user` y el validador `is_course_eligible_for_user` no verifican los atributos `age_min` y `age_max` de los cursos. Esto permite que alumnos menores de edad visualicen e inicien cursos para adultos, causando fallos en los tests del sistema (`tests/test_catalog.py`).

---

## 4. Próximos Pasos Recomendados

Para avanzar de forma óptima a la fase de desarrollo, sugerimos priorizar las siguientes tareas:
1. **Corregir el renderizado de layouts:** Reemplazar el uso de `<router-view />` por `<slot />` en los componentes de layout.
2. **Implementar el Endpoint Bulk:** Crear la ruta en FastAPI para la inserción masiva de preguntas del examen.
3. **Desarrollar el editor inline (tipo Google Forms):** Reemplazar las vistas fragmentadas por el componente unificado.
4. **Corregir los parámetros y variables mapeadas:** Unificar `q` en la búsqueda de estudiantes, resolver `progress_cached` y el flujo de descarga de CSV autenticado.
