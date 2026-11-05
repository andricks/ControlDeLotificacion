---
name: mongodb
description: Base de datos MongoDB Atlas con Beanie (ODM async) — diseño de colecciones, embebido vs referencia, dinero en Decimal128, transacciones, contadores de correlativos, índices, validación $jsonSchema, migraciones de datos, búsqueda de texto y seguridad contra inyección NoSQL. Usar al crear/modificar modelos, consultas, índices o scripts de migración.
---

# MongoDB Atlas + Beanie

Decisión: `docs/decisiones/ADR-002-mongodb-atlas.md`. Fuente de verdad del modelo: `docs/MODELO-DATOS.md` (actualizar en el mismo cambio).

## Conexión (backend/app/core/db.py)

```python
from beanie import init_beanie
from pymongo import AsyncMongoClient

cliente: AsyncMongoClient | None = None

async def conectar(settings) -> None:
    global cliente
    cliente = AsyncMongoClient(settings.mongodb_uri, tz_aware=True, uuidRepresentation="standard")
    await init_beanie(database=cliente[settings.mongodb_db], document_models=MODELOS)
```
Llamar en el `lifespan` de FastAPI. Tests: base separada (`MONGODB_DB=facturas_test`) que se borra al final; nunca tests contra la BD real.

## Diseño de colecciones: ¿embeber o referenciar?

| Situación | Decisión |
|---|---|
| Datos que solo existen dentro del padre y se leen juntos (colindancias de un lote, cuotas pactadas) | **Embeber** |
| Entidades con vida propia, reutilizadas (cliente, lote) | **Colección propia + referencia** (`cliente_id: PydanticObjectId`) |
| Crece sin límite o se consulta por separado (pagos/recibos) | **Colección propia** con `contrato_id` |
| Datos que deben quedar congelados legalmente (cliente al firmar) | **Instantánea embebida** además de la referencia |

## Modelo ejemplo

```python
from decimal import Decimal
from beanie import Document, DecimalAnnotation, Indexed, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel

class Pago(Document):
    contrato_id: PydanticObjectId
    numero_recibo: Indexed(int, unique=True)
    fecha_pago: date
    monto: DecimalAnnotation            # se guarda como Decimal128
    saldo_despues: DecimalAnnotation
    concepto: str
    anulado: bool = False
    creado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "pagos"
        indexes = [IndexModel([("contrato_id", ASCENDING), ("fecha_pago", ASCENDING)])]
```
> Verificar en la versión instalada de Beanie que `DecimalAnnotation` exista; si no, usar `Annotated[Decimal, BeforeValidator(...), PlainSerializer(Decimal128)]`.

## Correlativos atómicos (número de contrato / recibo)

```python
async def siguiente(nombre: str, session=None) -> int:
    doc = await db["contadores"].find_one_and_update(
        {"_id": nombre}, {"$inc": {"valor": 1}}, upsert=True,
        return_document=ReturnDocument.AFTER, session=session)
    return doc["valor"]
```
Nunca `count() + 1` (dos usuarios obtendrían el mismo número).

## Transacciones (Atlas = replica set)

```python
async with cliente.start_session() as s:
    async with await s.start_transaction():
        numero = await siguiente("recibo", session=s)
        await pago.insert(session=s)
        await contrato.update({"$inc": {"total_pagado": Decimal128(monto)}}, session=s)
        await registrar_auditoria(..., session=s)
```
Usar para cualquier operación que modifique más de un documento. Mantener transacciones cortas (sin generar PDFs dentro).

## Índices

- Declarados en `Settings.indexes` de cada modelo (Beanie los crea al iniciar).
- Únicos: `clientes.dpi` (parcial, si existe), `contratos.numero`, `pagos.numero_recibo`, `lotes.(proyecto, manzana, numero_lote)`.
- Consultas frecuentes: `contratos.cliente_id`, `contratos.estado`, `pagos.contrato_id + fecha_pago`.
- Texto: `IndexModel([("nombre", TEXT), ("dpi", TEXT)], default_language="spanish")` — una sola text index por colección.
- Revisar con `explain()` las consultas de listados.

## Validación en la BD ($jsonSchema)

Para `contratos` y `pagos`, crear validator en un script de migración (`collMod`) que exija campos obligatorios y `bsonType: "decimal"` en montos. Segunda línea de defensa si algún script escribe fuera de Beanie.

## Migraciones (sin Alembic)

- `backend/migraciones/NNNN_descripcion.py` con `async def aplicar(db)` y `async def revertir(db)`.
- Colección `_migraciones` registra cuáles se aplicaron; runner `python -m app.migrar`.
- Usar para: crear validators, renombrar campos, rellenar campos nuevos, transformar datos. Idempotentes.

## Seguridad

- **Inyección NoSQL:** jamás `find(request_json)` ni filtros con valores que puedan ser dict. Los filtros se construyen desde schemas Pydantic con tipos simples (`str`, `int`, `date`). Nunca `$where` ni `$function`.
- Ordenamiento: lista blanca de campos permitidos.
- Proyecciones: no devolver campos internos.
- Atlas: usuario con rol `readWrite` solo sobre la BD del proyecto; Network Access con IPs concretas (evitar `0.0.0.0/0` en producción); backups activados en tier de pago.

## Diagnóstico de conexión

- `python -m app.probar_conexion` (desde backend/) — nunca imprime la URI.
- `TLSV1_ALERT_INTERNAL_ERROR` / "SSL handshake failed" intermitente = **IP no permitida** en Atlas Network Access. La red de la oficina sale por **dos IPs públicas alternadas**; ambas deben estar en la lista. Si el proveedor cambia de IP, agregar la nueva.
- `code 18` = usuario/contraseña incorrectos. `ServerSelectionTimeoutError` = sin red o clúster pausado.

## Paginación

`find(filtro).sort(...).skip((pagina-1)*tamano).limit(tamano)` + `count()`. Para listados muy grandes, paginación por cursor (`_id > ultimo_id`).
