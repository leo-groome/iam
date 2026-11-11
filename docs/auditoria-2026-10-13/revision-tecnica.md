# Diagnóstico de tickets y prioridades

**Actualización:** las correcciones locales y sus pruebas están documentadas en [correcciones.md](correcciones.md). El diagnóstico siguiente conserva los hallazgos anteriores a los cambios. La aceptación E2E y publicación siguen pendientes.

Fecha: 13 de octubre de 2026. Inspección del checkout local; no se verificó que coincida con la versión desplegada. No se han corregido ni publicado los bugs en esta revisión.

## IAM-001 — Creación de curso

**Confirmado en código:** `AdminCursoDetalle.vue` captura los errores dentro de `saveCourse()` y solo usa `console.error`. `saveDrawer()` continúa con `closeDrawer()` incluso después de un rechazo. Para un curso nuevo, cerrar navega al listado y se pierde el formulario. Además, la navegación al curso creado se inicia sin esperar y después el cierre del drawer inicia otra navegación al listado.

Los `minlength` y `pattern` de los campos no se validan mediante submit de un formulario; Guardar es un botón que ejecuta una función. El backend exige título de 5–80, descripción corta de 10–500 (HTML incluido) y slug con un patrón estricto. El generador de slug no colapsa guiones repetidos: un título con ` - ` puede generar un slug inválido.

**Aún desconocido:** el rechazo concreto de la creación reportada (422, slug duplicado, permisos, error de DB u otro). No atribuirlo al backend sin response y persistencia.

**Corrección propuesta:** devolver resultado explícito o propagar error; cerrar solo ante éxito; mantener datos; mostrar error con campo; validar antes de enviar; esperar una única navegación; gestionar slug duplicado. Probar creación válida, rechazo, reintento y recarga.

## IAM-002 — Intentos

**Causa confirmada en el checkout para diagnósticos de módulo:** `AdminModuloDetalle.vue` envía `max_attempts`, pero `ModuleCreate` / `ModuleUpdate` no lo declaran. Pydantic descarta el extra. `Module` tampoco tiene columna; `ModuleResponse` y `ModuleAdminItem` no devuelven ese valor. Al recargar, la UI aplica `?? 3`. El objeto de módulo embebido en curso también omite `description`, por lo que al editar se carga una descripción vacía y un guardado puede sobrescribir la existente.

**Aplicación al alumno:** `get_module_exam` y `submit_module_exam` no comprueban un máximo de intentos. La UI afirma que al agotarlos se muestran respuestas y se avanza sin aprobar, pero el motor de progreso y la emisión de certificados exigen aprobación del diagnóstico. Persistir un campo no arregla por sí solo el flujo completo.

**Otra posible ubicación del ticket:** `AdminConfiguracion.vue` tiene un `max_attempts` global; esa pantalla no persiste nada: `saveConfig()` usa únicamente `setTimeout`, con un comentario MOCK. Confirmar cuál pantalla usó Cecilia.

**Corrección propuesta:** definir ámbito del límite; agregar columna, migración, esquemas de escritura/lectura y respuesta anidada; validar 1–10; contar intentos en inicio y entrega con protección frente a envíos concurrentes; mostrar al alumno el límite alcanzado. Probar 1 y otro valor, recarga, límite real y conservación del historial. Decidir cómo tratar intentos previos y alumnos que fallan su último intento antes de cambiar la progresión.

## IAM-003 — Retroalimentación

No hay un campo de retroalimentación por opción en el modelo `Option`, esquemas administrativos ni contrato `ExamResult`. Es una ampliación que requiere DB, API, editor y resultados; no basta añadir un textarea. Definir si se muestra tras cada entrega o al agotar intentos y cubrir preguntas de clase y de módulo. Mantenerla opcional y evitar exponer respuestas correctas en la API de inicio del examen.

## Hallazgos adicionales del código

| ID | Prioridad | Hallazgo | Evidencia / consecuencia |
| --- | --- | --- | --- |
| CODE-001 | Alta | Configuración global sin persistencia | `AdminConfiguracion.vue`: Guardar solo espera 800 ms; registro, mantenimiento, nota y certificados son controles sin implementación de guardado. |
| CODE-002 | Alta | Descripción de módulo ausente al editar | `ModuleAdminItem` no expone `description`; el formulario la inicializa a vacío y la reenvía. |
| CODE-003 | Media | Estado y certificado de curso sin conexión | Drawer de `AdminCursoDetalle.vue`: select sin `v-model`, checkbox fijo; no se envían al API. El endpoint de creación inicia borrador aunque el select diga Publicado. |
| CODE-004 | Media | Fallos de guardado de módulo silenciosos | `handleSave()` solo escribe en consola, sin confirmación ni mensaje visible. |

Son hallazgos de inspección, **no reproducciones de producción**. Su existencia en la versión desplegada queda pendiente.

## Orden de trabajo

1. Reproducir IAM-001 con cuenta de prueba, corregir manejo del formulario y causa del rechazo.
2. Precisar ámbito de IAM-002; corregir persistencia y límite real conjuntamente. Incluir descripción de módulo para evitar pérdida de contenido.
3. Ocultar o implementar controles simulados y resolver mensajes de guardado.
4. Definir e implementar IAM-003.
5. Ejecutar regresión administrativa y de alumno; después desplegar la infraestructura Docker a staging y cambiar producción.

Cada cierre debe incluir causa, pruebas, commit desplegado y fecha. Ningún ticket queda cerrado por esta revisión.

## Comprobaciones adicionales del código

Se ejecutaron directamente los esquemas Pydantic del proyecto:

```text
ModuleCreate(title='Modulo prueba', max_attempts=1)
→ {'title': 'Modulo prueba', 'description': '', 'order_index': None}
ModuleUpdate(max_attempts=1).model_dump(exclude_none=True)
→ {}
OptionCreate(texto='Respuesta', feedback='Explicacion')
→ {'texto': 'Respuesta', 'is_correct': False, 'order_index': 0}
CourseCreate(..., slug='curso---prueba')
→ ValidationError en slug: string_pattern_mismatch
```

El descarte de intentos y retroalimentación queda demostrado localmente, no solo inferido. La DB tiene un índice único sobre `Course.slug`; la creación no captura `IntegrityError` para traducir un slug duplicado a un error de negocio. Es otro caso de rechazo que la interfaz puede ocultar; no prueba que fuera el caso de Cecilia.

Pruebas existentes ejecutadas: `.venv/bin/pytest tests/test_admin.py tests/test_learning.py -q` → **48 passed**, 8 advertencias de deprecación de HTTP 422, en 18.74 s. Usaron SQLite local y autenticación simulada. No cubren el comportamiento de cierre del drawer Vue, la persistencia de `max_attempts` ni retroalimentación; que pasen no resuelve los tickets. No se modificó código de aplicación ni se ejecutaron migraciones.

### Alcance real de IAM-003

Hay dos editores: `AdminPreguntaDetalle.vue` (preguntas individuales y diagnósticos de módulo) y el editor integrado de `AdminTemaDetalle.vue` (preguntas de clase, guardado bulk). Ambos deben mantener retroalimentación al cargar, crear y guardar. El CRUD de creación construye `Option` enumerando campos explícitamente; ampliar únicamente el esquema Pydantic seguiría sin guardar la explicación. `ExamRunner.vue` solo presenta score/passed/message, sin detalle por respuesta; `ExamResult` tampoco lo devuelve.

### Defecto adicional al editar opciones existentes

`AdminPreguntaDetalle.vue` almacena textos en un array y actualiza las opciones originales por posición (`pregunta.options[i]`). Al agregar una opción, no crea un registro nuevo. Al quitarla, no borra el registro existente: desplaza textos hacia IDs anteriores y deja registros sobrantes. También `removeOption()` no ajusta el índice correcto cuando se elimina una opción anterior a la correcta. Ejemplo: quitar la opción 1 de cuatro, con la opción 2 correcta, puede marcar la antigua opción 3 como correcta. Corregir identidad por ID y guardar opciones de manera coherente antes de incorporar explicaciones asociadas a ellas.

### Diagnóstico de módulo en el alumno

Existen endpoints de inicio y entrega del examen de módulo, pero en el frontend revisado no se encontró un consumidor de `/modules/{id}/exam`; el runner consume únicamente exámenes de clase. Verificar el recorrido del diagnóstico en producción. La corrección del límite de módulos debe incluir un flujo de alumno que realmente use ese examen.
