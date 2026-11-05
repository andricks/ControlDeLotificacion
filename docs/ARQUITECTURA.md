# Arquitectura

## Vista general

```
┌──────────────────────┐     HTTPS/JSON      ┌───────────────────────────┐   TLS/Beanie  ┌──────────────┐
│ Frontend (React+Vite)│ ──────────────────▶ │ API FastAPI  /api/v1      │ ───────────▶ │ MongoDB Atlas│
│ SPA en español       │ ◀── PDF / ZIP ───── │ router→service→repository │              └──────────────┘
└──────────────────────┘                     │ pdf/ (leer + generar)     │ ──archivos──▶ storage/
                                             └───────────────────────────┘               originales/ generados/ miniaturas/
```

## Capas del backend

| Capa | Responsabilidad | Prohibido |
|---|---|---|
| `router.py` | HTTP: parámetros, auth/rol, `response_model`, códigos de estado | Consultas a BD, reglas de negocio |
| `service.py` | Reglas de negocio, cálculos, transacciones, auditoría | Conocer HTTP (`Request`, `HTTPException`) |
| `repository.py` | Consultas Beanie/PyMongo | Reglas de negocio |
| `models.py` | Mapeo ORM | Lógica |
| `pdf/` | Leer PDFs (extracción) y generar PDFs (plantillas) | Acceso a BD |
| `core/almacenamiento.py` | Guardar/leer/borrar archivos (interfaz intercambiable: disco → S3) | Rutas con texto del usuario |

## Flujos principales

### Subir documento con extracción
1. Frontend envía `multipart/form-data` → `POST /api/v1/archivos`.
2. Service valida tamaño + magic bytes, calcula SHA-256 (si existe → devuelve el existente).
3. Guarda en `storage/originales/aaaa/mm/<uuid>.pdf`, inserta `archivos`, commit (si falla, borra el archivo).
4. Extrae texto/metadatos (`pdf/lectura.py`); si requiere OCR → tarea en segundo plano.
5. Devuelve `archivo_id` + campos sugeridos → el usuario confirma en el formulario → se crea la factura/contrato/plano vinculado.

### Descargar PDF
1. `GET /api/v1/<recurso>/{id}/pdf` → verifica rol y existencia.
2. Service arma schema de detalle → `pdf/plantillas/<recurso>.py` devuelve bytes.
3. Se registra auditoría → `Response(application/pdf, Content-Disposition)`.

### Expediente / ZIP
- Expediente: pypdf une portada + ficha + adjuntos PDF (imágenes convertidas a página PDF).
- ZIP: `zipfile` en memoria, un PDF por documento + `indice.csv`; límite configurable por petición.

## Tareas en segundo plano

Fase inicial: `BackgroundTasks` de FastAPI (OCR, miniaturas). Si crece: cola (RQ/Celery + Redis) — requerirá ADR.

## Entornos y configuración

- `.env` (no versionado) con: `DATABASE_URL`, `JWT_SECRETO`, `JWT_MINUTOS`, `CORS_ORIGENES`, `STORAGE_DIR`, `MAX_MB_ARCHIVO`, `OCR_HABILITADO`, `TESSERACT_CMD`.
- Desarrollo: MongoDB Atlas (clúster M0, base `facturas`; tests en `facturas_test`), `uvicorn --reload`, `npm run dev` con proxy `/api` → `localhost:8000`.
- Producción (futuro): Nginx sirve el build del frontend y hace proxy a uvicorn/gunicorn; `storage/` en disco con respaldo.

## Herramientas de calidad

| Herramienta | Dónde | Ejecutada por |
|---|---|---|
| ruff (lint + formato) | backend | hook post-edición + `validar.py` |
| pytest | backend | `validar.py` |
| ESLint + Prettier | frontend | hook post-edición + `validar.py` |
| tsc (typecheck) | frontend | `validar.py` |
| Vitest | frontend | `validar.py` |
| vite build | frontend | `validar.py` (no en `--rapido`) |
