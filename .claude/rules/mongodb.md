---
paths:
  - "backend/app/**/models.py"
  - "backend/app/**/repository.py"
  - "backend/migraciones/**"
  - "backend/app/core/db.py"
---

# Reglas: MongoDB

- Montos con `DecimalAnnotation` / `Decimal128`; prohibido `float`.
- Operaciones sobre más de un documento → transacción (`start_session` + `start_transaction`).
- Correlativos (contrato, recibo) solo con la colección `contadores` y `$inc` atómico.
- Índices declarados en `Settings.indexes`; únicos para número de contrato, número de recibo y DPI.
- Filtros de consulta construidos desde tipos simples validados; nunca dicts del cliente, nunca `$where`/`$function`.
- Contratos guardan instantánea de cliente y lote al firmar.
- Cambios de estructura de datos existentes → script en `backend/migraciones/` (idempotente, con `revertir`).
- Actualizar `docs/MODELO-DATOS.md` en el mismo cambio.
- Tests contra una base `*_test` desechable, nunca contra la base real.
