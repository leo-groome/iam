# Correcciones locales de los tickets

13 de octubre de 2026. Cambios implementados en el checkout; pendientes de aplicar migración en el entorno de prueba, E2E y publicación. No se modificó producción.

## IAM-001

El formulario valida título, slug y descripciones; normaliza guiones del slug; conserva datos y muestra errores si falla el guardado. Solo navega al curso creado después de recibir su ID, con una única navegación. Editar un curso muestra confirmación y recarga los datos sin volver al listado. Los slugs duplicados devuelven HTTP 409 con un mensaje comprensible. Se retiraron los controles de estado/certificado que no guardaban nada y se dejó explícito el estado real; Publicar sigue siendo una acción separada.

El rechazo original de Cecilia aún necesita reproducción con sus datos y el entorno desplegado. Estas correcciones cubren las causas identificadas en código y eliminan la pérdida silenciosa del formulario.

## IAM-002

Los módulos y clases guardan `max_attempts` (entero 1–10, predeterminado 3), lo devuelven al editor y lo aplican tanto al abrir como al entregar el examen. La entrega bloquea la fila de matrícula en PostgreSQL para serializar solicitudes simultáneas del mismo alumno/curso antes de contar intentos. Un token obtenido antes de agotar el límite no permite otra entrega después.

Todos los intentos existentes cuentan. No se borran respuestas ni calificaciones. Agotar intentos sin aprobar no aprueba el examen ni desbloquea un certificado: aparece un mensaje para contactar al administrador, quien puede aumentar el límite dentro del rango permitido. El límite de una clase es independiente del diagnóstico de módulo.

La respuesta anidada del curso ahora incluye descripción y límite del módulo, evitando sobrescribir la descripción con un valor vacío al editar. El formulario muestra errores/confirmación y navega al módulo recién creado. El alumno tiene acceso al diagnóstico desde el curso y al terminar las clases del módulo.

La página global de Configuración dejó de presentar valores simulados y un botón de guardado falso. Ahora informa que esos ajustes no están disponibles y dirige a la configuración real por clase/módulo; no se implementó una nueva plataforma de ajustes globales.

## IAM-003

Retroalimentación opcional de texto por opción, hasta 5000 caracteres, disponible en ambos editores. Persistencia en DB y contratos administrativos, con explicación vacía por defecto para opciones existentes. Después de entregar, la API devuelve la explicación y correctitud de las opciones seleccionadas; el runner las muestra. La API de inicio no expone correctitud ni explicaciones. El enunciado se sanitiza y la explicación se renderiza como texto.

La edición individual de una pregunta guarda enunciado y opciones en una transacción, preserva IDs de las opciones conservadas y crea/elimina las restantes. Eliminar una opción anterior a la correcta ya no desplaza erróneamente la selección correcta. No se recalculan notas históricas.

También se agregó nombre accesible y acceso por teclado a los botones de mostrar/ocultar contraseña.

## Validación realizada

- Suite completa del backend: **121 passed**, 16 advertencias existentes sobre HTTP 422 obsoleto.
- Regresiones: slug duplicado; límites 1/2 y valores inválidos; descripción después de recargar; edición de opciones por ID, retroalimentación y rechazo de IDs ajenos; conservación del historial; inicio/entrega bloqueados al agotar intentos; token obtenido previamente; explicaciones solo después de entregar.
- SQL de la migración generado y revisado con Alembic en modo offline. No se ejecutó contra PostgreSQL real; SQLite no verifica los bloqueos de concurrencia de PostgreSQL.
- Tipos OpenAPI del frontend regenerados.
- Build Vite final correcto. El chequeo global `vue-tsc` continúa encontrando errores de tipos preexistentes en otras pantallas/dependencias; las pantallas modificadas para los tickets y el runner no reportan errores en la comprobación final.
- `git diff --check` correcto.

## Migración y E2E siguientes

Aplicar **en una DB de prueba** `alembic upgrade head`, que incorpora `g5c6d7e8f9a0` desde `f4b5c6d7e8a9`. Desplegar API y frontend compatibles. La migración agrega columnas con defaults y no borra historial. Antes de producción, realizar backup y verificar la versión de Alembic; no ejecutar downgrade automáticamente, porque elimina las columnas de límites y explicaciones.

E2E con admin y alumno de prueba:

1. Crear curso válido; comprobar listado, recarga y edición. Probar slug duplicado y rechazo de guardado, conservar formulario y reintentar.
2. Guardar 1 intento en clase y módulo, volver a abrir y recargar. Completar el primero y comprobar rechazo del segundo. Probar 2 intentos y cambio de límite con historial previo.
3. Validar entregas concurrentes contra PostgreSQL real: un solo intento debe persistir cuando queda uno disponible.
4. Guardar/editar explicaciones en ambos editores y verificar opciones seleccionadas en resultados, incluidas opciones sin explicación, en escritorio/móvil.
5. Agregar/eliminar opciones existentes, comprobar correcta y notas anteriores. Recorrer diagnóstico de módulo, bloqueo/desbloqueo de la siguiente clase y certificado.

Los tickets quedan implementados localmente, **pendientes de aceptación E2E y publicación**, no cerrados en producción.
