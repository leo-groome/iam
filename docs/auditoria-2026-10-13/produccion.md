# Campus IAM — revisión de producción

Fecha: 13 de octubre de 2026. URL: https://iam-campus.vercel.app. Herramienta: Agent Browser, sesión `iam-audit`.

## Alcance y límites

Revisión sin autenticación: acceso a `/admin`, login en escritorio y móvil (390 × 844), navegación a recuperación de contraseña y auditoría axe WCAG A/AA. `/admin` redirige a `/login?next=/admin`, como corresponde sin sesión. No se enviaron correos, crearon cuentas ni modificaron cursos o calificaciones. No había perfiles de autenticación guardados al revisar.

La revisión del panel y de los flujos del alumno está **pendiente de una cuenta de prueba**. Los tickets originales no están reproducidos en producción; el diagnóstico de código se documenta por separado en `revision-tecnica.md`.

## Resumen de bugs confirmados en navegador

| Severidad del producto | Cantidad |
| --- | ---: |
| Crítica | 0 |
| Alta | 0 |
| Media | 1 |
| Baja | 0 |

### PROD-001 — El botón de visibilidad de contraseña no tiene nombre accesible

- Severidad: media. Categoría: accesibilidad.
- URL: https://iam-campus.vercel.app/login
- Evidencia: [captura anotada](screenshots/login-a11y.png), referencia 21 sin nombre; axe `button-name`, selector `.inset-y-0`.
- Reproducción: abrir login y consultar el árbol de accesibilidad o ejecutar `agent-browser --session iam-audit a11y --tags wcag2a,wcag2aa`. Confirmado dos veces, en escritorio y móvil.
- Resultado: el control se anuncia únicamente como botón; el lector de pantalla no comunica su propósito.
- Esperado: nombre «Mostrar contraseña» / «Ocultar contraseña» según estado; funcionamiento por teclado.
- Video: N/A; defecto presente al cargar.
- Nota: axe clasifica la regla como `critical`; aquí se usa severidad media de producto porque el formulario sigue operando.

## Observaciones sin clasificación de bug

- No se observaron excepciones en `agent-browser errors` durante el tramo revisado.
- La recuperación de contraseña abre su página. No se verificó el envío ni la recepción del código.
- El contraste de seis elementos del login en escritorio quedó inicialmente como `incomplete` en axe; requiere revisión manual y no constituye un defecto confirmado.
- Capturas de referencia: [escritorio](screenshots/login-desktop.png), [móvil](screenshots/login-mobile.png), [recuperación](screenshots/recuperacion.png).

## Revisión autenticada pendiente

1. Crear un curso **borrador de prueba** con datos válidos; registrar request/response sin tokens, comprobar listado, recarga y edición.
2. Probar validaciones, slug duplicado y fallo de red: conservar el formulario y mostrar error.
3. Identificar el cuestionario de Hogares de Protección: examen de clase, diagnóstico de módulo o configuración global. Guardar 1 intento, recargar y probar el límite con alumno de prueba.
4. Comprobar editor de opciones y resultados, subida de portada y medios, progreso y certificado.
5. Revisar cada página administrativa en móvil; grabar los defectos interactivos con pasos y capturas.

No cerrar IAM-001/IAM-002 únicamente con una prueba visual de guardado: verificar persistencia y comportamiento del alumno.
