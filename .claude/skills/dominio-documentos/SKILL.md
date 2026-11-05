---
name: dominio-documentos
description: Conocimiento de negocio para facturas, contratos y planos de terrenos en Guatemala — FEL/SAT, NIT, DPI, IVA 12 %, datos registrales (finca, folio, libro), tipos de contrato, estados y ciclo de vida de cada documento, y qué relaciones existen entre ellos. Usar al modelar entidades, escribir reglas de negocio o validar datos de documentos.
---

# Dominio: facturas, contratos y planos (Guatemala)

> Esto es orientación técnica, no asesoría legal/fiscal. Ante dudas normativas, marcarlo en `docs/REQUISITOS.md` como pregunta abierta para el usuario.

## Entidad central: el terreno

El sistema gira alrededor del **terreno/inmueble**. Un terreno tiene:
- Datos registrales del **Registro General de la Propiedad (RGP)**: número de **finca**, **folio**, **libro** (y a veces "de <departamento>").
- Ubicación: departamento, municipio, dirección/aldea, coordenadas (sistema GTM o UTM 15/16N).
- Área en m² (convertir varas² y manzanas — ver skill leer-pdf/referencia-campos.md).
- Relaciones: **N planos** (versiones), **N contratos**, **N facturas**.

## Partes (personas y empresas)

- Persona individual: nombre, **DPI/CUI** (13 dígitos), NIT opcional.
- Persona jurídica: razón social, NIT, representante legal (persona individual).
- Una parte puede ser cliente, proveedor, vendedor, comprador, arrendante, arrendatario, testigo… el **rol** vive en la relación (`contrato_partes.rol`), no en la parte.
- **NIT** con dígito verificador módulo 11 (puede ser `K`); `CF` = Consumidor Final.

## Facturas

- En Guatemala la factura válida fiscalmente es el **DTE FEL** certificado por un **certificador** autorizado por la SAT. Tiene: serie, número DTE, **número de autorización (UUID)**, fecha de certificación, NIT emisor/receptor.
- **Este sistema registra y archiva facturas** (emitidas o recibidas) y puede adjuntar el PDF/XML FEL original. **No certifica** DTE. Una integración con un certificador sería una fase futura (ADR aparte).
- IVA general **12 %**; los precios en Guatemala suelen incluir IVA: `iva = total / 1.12 × 0.12`. Guardar `subtotal_sin_iva`, `iva`, `total` calculados con `Decimal` y redondeo `ROUND_HALF_UP` a 2 decimales.
- Tipos DTE comunes: FACT (factura), FCAM (cambiaria), FPEQ (pequeño contribuyente — no desglosa IVA), NCRE (nota de crédito), NDEB (nota de débito), RECI (recibo).
- **Estados:** `borrador → registrada → pagada` | `registrada → anulada`. Una factura anulada o pagada no se edita (solo notas). Anular exige motivo.
- Dirección: `emitida` (nosotros emitimos) o `recibida` (proveedor nos emite).
- Unicidad: (emisor, serie, número) y número de autorización si existe.

## Contratos

- Tipos: compraventa, promesa de compraventa, arrendamiento, usufructo, servicios (medición, construcción), otro.
- Datos: número interno, tipo, fecha de firma, vigencia (inicio/fin), monto y moneda, forma de pago, notario (nombre, colegiado), terreno relacionado, partes con rol.
- **Estados:** `borrador → vigente → finalizado` | `vigente → rescindido`. Alertar contratos por vencer (30 días).
- Un contrato puede tener varias facturas asociadas (pagos/cuotas) → mostrar saldo pendiente = monto − Σ facturas pagadas.
- Anexos: escritura escaneada, plano, DPIs (datos sensibles → acceso restringido).

## Planos

- Datos: terreno, código/número de plano, título, versión, escala (1:500, 1:1000…), fecha de elaboración, profesional (ingeniero/arquitecto/agrimensor) y **número de colegiado**, área medida, colindancias (norte/sur/este/oeste con medida y colindante), sistema de coordenadas.
- Archivo: PDF (preferido) o imagen (JPG/PNG/TIFF); DWG/DXF solo se archiva, no se procesa.
- Versionado: un plano nuevo del mismo terreno no borra el anterior; marca `vigente = true` solo en el último.
- Generar **ficha técnica PDF**: datos del terreno + tabla de colindancias + miniatura/plano embebido.

## Expediente

"Descargar expediente" de un terreno o contrato = un PDF que une: portada/índice generado + ficha de datos + todos los PDFs adjuntos en orden cronológico (pypdf). Alternativa: ZIP con archivos sueltos + índice.

## Datos sensibles

DPI, direcciones personales y montos → solo roles autorizados; enmascarar DPI en listados (`•••• ••••• 0101`); toda descarga queda auditada.
