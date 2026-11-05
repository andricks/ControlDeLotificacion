# ADR-002: MongoDB Atlas como base de datos (reemplaza PostgreSQL)

- **Estado:** Aceptado (decisión del usuario)
- **Fecha:** 2026-09-29
- **Reemplaza:** la fila "BD" y "ORM / migraciones" de ADR-001

## Decisión

| Área | Antes | Ahora |
|---|---|---|
| Base de datos | PostgreSQL 16 | **MongoDB Atlas** (clúster en la nube, M0 gratis para desarrollo) |
| Acceso desde Python | SQLAlchemy + Alembic | **Beanie 2.x** (ODM sobre PyMongo async + Pydantic v2) |
| Cambios de esquema | Migraciones Alembic | Modelos Beanie + **scripts de migración versionados** en `backend/migraciones/` + índices declarados en cada modelo |
| Búsqueda de texto | tsvector | Índice de texto de MongoDB (`$text`, idioma `spanish`); Atlas Search a futuro |

## Reglas que esto impone

1. **Dinero como `Decimal128`** (en Beanie: `DecimalAnnotation`); nunca `float`.
2. **Transacciones** (Atlas es replica set) para operaciones que tocan varias colecciones: registrar pago = insertar pago + actualizar saldo del contrato + auditoría.
3. **Números correlativos** (contrato, recibo) con colección `contadores` y `find_one_and_update($inc)` atómico.
4. **Validación doble:** Pydantic en la app + `$jsonSchema` validator en las colecciones críticas (contratos, pagos).
5. **Instantánea legal:** el contrato guarda una copia de los datos del cliente y del lote *tal como se firmaron*; si luego el cliente cambia de dirección, el contrato PDF no cambia.
6. **Seguridad NoSQL:** nunca pasar dicts del cliente directamente a filtros de consulta (inyección de operadores `$ne`, `$gt`, `$where`); filtros construidos solo desde schemas validados.
7. La cadena de conexión (`MONGODB_URI`) vive solo en `.env`. En Atlas: usuario de BD con permisos mínimos y lista de IPs permitidas.

## Consecuencias

- (+) Esquema flexible mientras se descubren los campos reales de los documentos en papel.
- (+) Sin servidor de BD que instalar ni mantener; accesible desde varias computadoras.
- (−) Se requiere internet para desarrollar y usar el sistema.
- (−) M0 gratis: 512 MB — suficiente para datos; **los archivos (PDF/fotos) se guardan en disco (`storage/`), no en Mongo**.
- (−) Integridad referencial la garantiza la aplicación, no la BD → tests obligatorios de reglas de negocio.
