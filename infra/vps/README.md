# Campus IAM en un VPS

Base preparada para frontend Vue, backend FastAPI y landing Astro. No está desplegada. Requiere servidor, dos dominios y las credenciales actuales. Mantiene Neon (DB y autenticación), R2/Worker y Resend como servicios externos en la primera fase.

Validación local del 13 de octubre de 2026: `docker compose config --no-env-resolution --quiet`, builds de las tres imágenes, `nginx -t` en ambas imágenes estáticas e importación del backend/función health con variables de ejemplo y red deshabilitada: correctos. Builds locales Vite/Astro también correctos. No se probó todavía el conjunto en ejecución, TLS, migraciones contra PostgreSQL ni integración Auth/R2/Resend. Las imágenes locales incorporan dominios ficticios y deben reconstruirse con las URLs reales.

## Antes de elegir servidor

Obtener facturas y consumo de Vercel, Railway, Neon, R2 y Resend; cantidad de usuarios simultáneos, CPU/RAM y tamaño de DB/media. No hay evidencia suficiente para estimar ahorro ni dimensionar un VPS. Construir imágenes en CI evita que el servidor de producción tenga que soportar los builds de Node.

Un VPS sustituye el alojamiento de las aplicaciones; no elimina por sí solo los costos de DB, autenticación, almacenamiento o correo. Migrar PostgreSQL y reemplazar Neon Auth es una segunda decisión: `app/db.py` exige SSL, Alembic usa funcionalidades PostgreSQL y los usuarios dependen del proveedor de autenticación. No copiar tablas y asumir que el login seguirá funcionando.

## Configuración

Desde este directorio:

```bash
cp .env.example .env
cp ../../apps/backend/.env.example backend.env
chmod 600 .env backend.env
```

Editar `.env` con **dos dominios distintos** y la URL pública real de Neon Auth. Editar `backend.env` con valores reales de DB/R2/Resend y:

- `FRONTEND_URL=https://<CAMPUS_DOMAIN>`
- `CERTIFICATE_VERIFY_BASE_URL=https://<CAMPUS_DOMAIN>`
- `NEON_AUTH_URL`: el mismo proveedor y proyecto actuales.
- `MEDIA_JWT_SECRET`: conservar el secreto compartido con el Worker.
- `ALLOW_MOCK_AUTH` se fuerza a false en Compose.

No copiar `.env` al frontend ni pasar contraseñas como build args. Las URLs de API y Auth del navegador son públicas y quedan incorporadas en el build; cambiarlas requiere reconstruir la imagen.

## Preparar y verificar en staging

1. Corregir IAM-001/IAM-002 y validar con cuenta admin y alumno de prueba antes del corte.
2. Crear copia de seguridad verificable de Neon, comprobar versión Alembic y documentar restauración. Para staging usar una rama/copia de DB y entorno de Auth apropiado; nunca ejecutar migraciones de ensayo contra producción.
3. Permitir los dominios nuevos en Neon Auth (orígenes/retornos OAuth), proveedor Google y CORS de R2 y del Worker. Revisar `infra/worker/wrangler.toml` y su allowlist; conservar el despliegue del Worker en Cloudflare.
4. Configurar DNS A/AAAA al VPS; abrir 80/443. Caddy obtiene y renueva TLS. No usar una dirección AAAA que no llegue al servidor.
5. Ejecutar:

```bash
docker compose --env-file .env config --quiet
docker compose --env-file .env build
docker compose --env-file .env up -d
docker compose --env-file .env ps -a
docker compose --env-file .env logs --tail=100 migrate backend proxy
```

No pegar logs con credenciales o JWT en reportes. `migrate` debe terminar con código 0; el proxy espera los healthchecks. `/health` verifica que el proceso responde, **no** que DB/R2/Auth funcionan. Comprobar login, creación y recarga de curso, intentos, medios (PUT y Range), progreso y certificados por separado.

Solo el proxy publica puertos. Certificados TLS se conservan en volúmenes de Caddy; hacer backup de ellos. Logs rotan a 3 × 10 MB por servicio. Las imágenes base usan tags móviles: antes de producción fijar digests aprobados y automatizar sus actualizaciones. Registrar commit y `RELEASE_TAG` de cada release, construirlo en CI y guardar las imágenes en un registro para rollback.

## Corte y reversión

Usar un dominio propio: el dominio `*.vercel.app` sigue perteneciendo a Vercel y no puede dirigirse al VPS. Reducir TTL previamente, programar ventana de mantenimiento, respaldar DB y congelar cambios administrativos durante migraciones. Verificar rutas de autenticación y enlaces/certificados existentes; mantener Vercel/Railway disponibles hasta completar la regresión.

En releases siguientes, ejecutar deliberadamente las migraciones para cada versión antes de iniciar su API. `docker compose restart` **no** vuelve a ejecutar `migrate`. Conservar release anterior y comprobar compatibilidad de esquema antes de revertir imágenes. No ejecutar `alembic downgrade` automáticamente ni `docker compose down -v` (borra volúmenes).

Si falla el corte, devolver DNS/URLs a Vercel/Railway y la imagen compatible anterior. Una reversión de DB requiere el plan de restauración y manejo de escrituras posteriores al backup; no es equivalente a revertir DNS.

## Referencias

- [Orden de arranque y dependencias de Compose](https://docs.docker.com/compose/how-tos/startup-order/): migraciones con `service_completed_successfully`, readiness con `service_healthy`.
- [HTTPS automático de Caddy](https://caddyserver.com/docs/automatic-https).
- [Secretos de build de Docker](https://docs.docker.com/build/building/secrets/): no usar ARG/ENV para credenciales.
