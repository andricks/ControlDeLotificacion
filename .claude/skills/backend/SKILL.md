---
name: backend
description: Desarrollo del backend con FastAPI + Beanie (MongoDB Atlas) + Pydantic v2 — estructura por módulos de dominio, endpoints CRUD, autenticación JWT con roles, subida segura de archivos, paginación, auditoría y tests. Usar al crear o modificar cualquier cosa en backend/.
---

# Backend (FastAPI)

## Estructura por módulo de dominio

```
backend/
  app/
    main.py                  # crea FastAPI, registra routers, CORS, handlers de error
    core/
      config.py              # Settings(BaseSettings) leído de .env
      db.py                  # AsyncMongoClient + init_beanie (en lifespan) — ver skill mongodb
      seguridad.py           # hash bcrypt/argon2, JWT, usuario_actual, requiere_rol()
      errores.py             # NoEncontrado, ReglaNegocio, SinPermiso + handler
      almacenamiento.py      # guardar/leer/borrar archivos (interfaz; impl. disco local)
    modules/
      clientes/  lotes/  contratos/  pagos/  facturas/  planos/  archivos/  usuarios/  auditoria/
        models.py            # Beanie Document (colección, índices)
        schemas.py           # Pydantic: XCrear, XActualizar, XLeer, XDetalle, XFiltros
        repository.py        # consultas (select/insert) — sin reglas de negocio
        service.py           # reglas de negocio, transacciones, auditoría
        router.py            # HTTP: valida, llama service, devuelve schema
    pdf/                     # ver skills leer-pdf y generar-pdf
  migraciones/               # scripts NNNN_*.py (aplicar/revertir), runner app/migrar.py
  tests/
  pyproject.toml             # dependencias + config ruff/pytest/mypy
```

Dependencias en una sola dirección: `router → service → repository → models`. El router **nunca** consulta la BD directamente.

## Convenciones de API

- Prefijo `/api/v1`. Recursos en plural: `/facturas`, `/contratos`, `/planos`, `/terrenos`, `/partes`.
- `GET /facturas?pagina=1&tamano=20&buscar=...&desde=...&hasta=...&estado=...&orden=-fecha_emision`
- Respuesta paginada: `{"items": [...], "total": 134, "pagina": 1, "tamano": 20}` (tamaño máx. 100).
- `POST` → 201 con el recurso; `PATCH` para actualizar parcial; `DELETE` → **borrado lógico** (`eliminado_en`) para documentos legales.
- Descargas: `GET /facturas/{id}/pdf`, `GET /contratos/{id}/pdf`, `GET /planos/{id}/pdf`, `GET /archivos/{id}/descargar`, `POST /exportar/zip`.
- Documentación automática en `/docs` (Swagger) — mantener `summary` y `description` en español.

## Schemas Pydantic (ejemplo)

```python
class FacturaLineaCrear(BaseModel):
    descripcion: str = Field(min_length=1, max_length=500)
    cantidad: Decimal = Field(gt=0, max_digits=12, decimal_places=4)
    precio_unitario: Decimal = Field(ge=0, max_digits=14, decimal_places=2)

class FacturaCrear(BaseModel):
    serie: str = Field(max_length=20)
    numero: str = Field(max_length=20)
    fecha_emision: date
    receptor_id: int
    moneda: Literal["GTQ", "USD"] = "GTQ"
    lineas: list[FacturaLineaCrear] = Field(min_length=1)

    @field_validator("fecha_emision")
    @classmethod
    def no_futura(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("La fecha de emisión no puede ser futura")
        return v
```

Totales (subtotal, IVA, total) los **calcula el servicio**, no se aceptan del cliente.

## Seguridad

- Contraseñas: `argon2` (passlib/argon2-cffi). JWT de acceso corto (15–30 min) + refresh.
- Roles: `admin` (todo), `operador` (crear/editar), `consulta` (leer/descargar). Dependencia `requiere_rol("operador")`.
- CORS solo para el origen del frontend (desde `.env`).
- Rate limit en login.
- **Subida de archivos** (`archivos/service.py`):
  1. Límite de tamaño (p. ej. 25 MB; planos hasta 100 MB) leyendo por bloques.
  2. Verificar tipo real por magic bytes (PDF `%PDF-`, PNG, JPEG, TIFF); ignorar extensión y `content-type` del cliente.
  3. SHA-256 → detectar duplicados.
  4. Guardar como `storage/originales/aaaa/mm/<uuid>.<ext>`; el nombre original solo en BD.
  5. Nunca construir rutas con texto del usuario (path traversal).
- Toda acción de crear/editar/eliminar/descargar → `auditoria.registrar(...)`.

## Async y transacciones

- Endpoints y services `async def` (Beanie es asíncrono); nunca bloquear el event loop — generar PDFs con `await asyncio.to_thread(construir_pdf, datos)`.
- Operaciones multi-documento dentro de una transacción de MongoDB (ver skill `mongodb`).
- Operaciones que tocan BD + disco: escribir archivo → insertar documento; si falla la inserción, borrar el archivo.
- IDs en la API como string (`PydanticObjectId`); validar formato → 404 si inválido.

## Tests

- `httpx.AsyncClient` + `ASGITransport` con `pytest-asyncio`; base `facturas_test` en Atlas que se vacía entre tests (nunca la base real).
- Fixture `cliente_autenticado(rol)` para probar permisos.
- Probar cada endpoint: 2xx, 401, 403, 404, 422 y reglas de negocio.

## Arranque

```powershell
cd backend
python -m venv .venv ; .venv\Scripts\activate
pip install -e ".[dev]"
python -m app.migrar
uvicorn app.main:app --reload
```
