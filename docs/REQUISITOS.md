# Requisitos

## Objetivo

Centralizar y sistematizar la información de **facturas, contratos y planos de terrenos**: registrarlos, adjuntar sus archivos originales, relacionarlos entre sí (por terreno, cliente y contrato), buscarlos rápidamente y **descargar cualquier documento, expediente o reporte en PDF**.

## Usuarios y roles

| Rol | Puede |
|---|---|
| `admin` | Todo, incluida gestión de usuarios y consulta de auditoría |
| `operador` | Crear, editar, anular, subir archivos, descargar |
| `consulta` | Ver, buscar y descargar |

## Requisitos funcionales

### RF-01 Autenticación
- Inicio/cierre de sesión con correo y contraseña; sesión con expiración.

### RF-02 Partes (clientes, proveedores, personas)
- CRUD de personas individuales y jurídicas con NIT (validado) y DPI.

### RF-03 Terrenos
- CRUD con datos registrales (finca, folio, libro), ubicación, área (conversión de varas²/manzanas a m²).
- Vista de expediente: planos, contratos y facturas relacionadas.

### RF-04 Facturas
- Registrar facturas emitidas y recibidas con líneas de detalle; cálculo automático de IVA (12 %) y totales.
- Adjuntar PDF/XML FEL original; extraer datos del PDF como sugerencia.
- Estados: borrador, registrada, pagada, anulada (con motivo).
- Relacionar opcionalmente con contrato y/o terreno.

### RF-05 Contratos
- Registrar contratos con tipo, partes y rol de cada una, vigencia, monto, notario, terreno.
- Adjuntar escritura/documento escaneado. Alertas de contratos por vencer (30 días).
- Saldo del contrato = monto − facturas pagadas asociadas.

### RF-06 Planos
- Registrar planos por terreno con versión, escala, profesional y colegiado, colindancias; adjuntar PDF/imagen.
- Miniatura y visor en la app.

### RF-07 Búsqueda
- Búsqueda global por número, serie, NIT, nombre, finca/folio/libro y **texto contenido en los PDFs**.
- Filtros por fecha, estado, tipo, terreno, parte.

### RF-08 Descargas PDF (requisito central)
- PDF individual de: factura, contrato (ficha), plano (ficha técnica), terreno (expediente).
- Descarga del archivo original adjunto.
- **Expediente completo** (PDF unido: portada + fichas + adjuntos).
- **Descarga masiva** de seleccionados en ZIP.
- Reportes en PDF: facturación por periodo, contratos por vencer, listado de terrenos.

### RF-09 Auditoría
- Registro de quién creó, editó, anuló, eliminó o descargó qué y cuándo; consulta para admin.

### RF-10 Dashboard
- Totales del mes, facturas pendientes de pago, contratos por vencer, últimos documentos.

## Requisitos no funcionales

- **Seguridad:** ver `.claude/rules/seguridad.md`; contraseñas con argon2; HTTPS en producción.
- **Rendimiento:** listados < 1 s con 10 000 registros; generación de PDF individual < 3 s.
- **Almacenamiento:** archivos hasta 25 MB (planos hasta 100 MB); deduplicación por SHA-256.
- **Usabilidad:** interfaz en español, responsive, accesible (WCAG AA).
- **Respaldo:** procedimiento documentado de respaldo de BD + `storage/`.
- **Trazabilidad:** borrado lógico; nada se pierde.

## Preguntas abiertas (resolver con el usuario)

- [ ] ¿Se emiten facturas desde el sistema (requiere certificador FEL) o solo se registran/archivan?
- [ ] ¿Una sola empresa emisora o varias?
- [ ] ¿Moneda USD además de GTQ?
- [ ] ¿Se necesita acceso fuera de la oficina (despliegue en la nube) o solo red local?
- [ ] ¿Formatos de planos a soportar además de PDF/imagen (DWG)?
- [ ] ¿Cuántos usuarios simultáneos aproximadamente?
