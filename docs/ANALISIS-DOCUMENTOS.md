# Análisis de documentos en papel (fuente: `documentos-muestra/`, no versionado)

Documento analizado: *CONTRATO DE COMPRA VENTA Y RECIBO.pdf* (3 páginas, fotos). Aquí solo se describen **campos y reglas**; los datos personales reales no se copian a este archivo.

## Emisor (datos fijos → configuración del sistema)

- Empresa: **Inmobiliaria Estrada** — proyecto **Lotificación "Tablon Campestre2"** (migraciones 0003, 0004 y 0005; el formulario en papel analizado traía los datos de otro emisor).
- Oficinas: San Pedro Pinula, Jalapa, Kilómetro 124.5, Residenciales Monaco. Teléfono: 5381-4009.
- Proyecto: San Pedro Pinula, Jalapa, Kilómetro 124.5, Residenciales Monaco.
- Lugar de pago (condiciones generales): 6a Calle y 8a Avenida 5-71 zona 3, Barrio El Chaparrón, Jutiapa.
- Representante que firma como propietario: consta en la legalización notarial.

## Página 1 — Promesa de Compra Venta (formulario con correlativo impreso Nº 00184)

| Sección | Campos |
|---|---|
| Encabezado | número de promesa (correlativo) |
| Datos del comprador | nombres y apellidos, dirección, teléfono, DPI, NIT, correo, fecha de nacimiento, edad, nacionalidad, estado civil, nº de personas que dependen, profesión/actividad, empresa donde trabaja, dirección y teléfono del trabajo, puesto, tiempo de trabajo, ingreso mensual, otros ingresos |
| Cónyuge, familiar o gestor | nombres y apellidos, dirección, teléfono, DPI, correo, fecha de nacimiento, edad, nacionalidad, profesión/actividad |
| Dependientes (hasta 5) | nombre, edad, nº de DPI |
| Identificación del inmueble | lote nº, área total (m²), finca, folio, libro, "de" (departamento del registro) |
| Condiciones | precio del terreno, mejoras al terreno, total, (−) enganche, (−) otros descuentos, saldo a pagar |
| Enganche fraccionado | hasta 4 filas de fecha + monto |
| Financiamiento | plazo en años, cuota nivelada mensual, tasa de interés anual variable, fecha de la primera cuota, otras condiciones de la negociación (texto libre) |
| Cláusula de arras | desistimiento → pierde 20 % del precio o 50 % de lo pagado, lo que sea mayor |
| Cierre | día, mes y año de firma; firma del comprador y del propietario |
| Legalización notarial | ciudad, día, mes, año, notario, representante de Inmobiliaria Estrada (en el ejemplo, **en blanco**) |

## Página 2 — Condiciones generales (texto legal fijo)

Cláusulas: promesa de compra-venta · cuotas e intereses · pagos a capital (mínimo Q 2,000.00) · recargos por mora (5 días de gracia, luego 5 % mensual por cuota vencida) · lugar de pago · posesión del inmueble · traspasos o desistimientos · obras de urbanización incluidas · cargos no incluidos · limitaciones de uso del lote (a–h) · incumplimiento · casos en que el vendedor puede dejar sin efecto · domicilio y aceptación.

⚠️ La foto está **cortada en el margen derecho y con poco contraste**: no se puede transcribir el texto completo con fidelidad. Se necesita una foto/escaneo más claro de esta página (o el texto en Word) para reproducirla en el PDF.

## Página 3 — Recibo de Caja

| Campo | Observación |
|---|---|
| Número | "FEL 2540" → ¿correlativo del recibo o número de factura FEL asociada? (confirmar) |
| Lugar y fecha | "Jalapa, 4 de noviembre del 2025" |
| Recibimos de | nombre del comprador |
| Monto en números y en letras | el sistema debe generar las letras automáticamente |
| Correspondiente a los lotes No. | plural → un cliente puede tener más de un lote |
| En concepto de | enganche (monto) **o** cuota nivelada nº X del mes Y |
| Desglose | capital, intereses, (+) recargo por mora, (+) abono a capital, (+) otros, total |
| Saldo | saldo anterior, (−) este pago, saldo actual |
| Boletas relacionadas | número de boleta / número de cuenta bancaria (puede haber varias) |
| Firma y sello | "RECIBIDO" + sello de caja |

## Validaciones realizadas sobre el ejemplo

| Verificación | Resultado |
|---|---|
| Precio terreno + mejoras = total | ✅ 20,000.00 + 102,400.00 = 122,400.00 |
| Total − enganche − descuentos = saldo | ✅ 122,400.00 − 10,000.00 − 0.00 = 112,400.00 |
| Enganche fraccionado = enganche | ✅ una fila por 10,000.00 |
| Edades vs. fecha de nacimiento a la fecha de firma | ✅ ambas coinciden |
| NIT del comprador (módulo 11) | ✅ válido |
| DPI comprador y cónyuge (dígito verificador + depto/municipio) | ✅ válidos; código 21-01 = Jalapa, Jalapa |
| Plazo "1 año" con cuota 10,219.00 | ⚠️ 12 cuotas = 122,628.00 ≠ 112,400.00. Cuadra con **11 cuotas** (feb–dic 2025): 10 de 10,219.00 + última de **10,210.00** |
| Saldo anterior del recibo (cuota 9) | ✅ 112,400.00 − 8 × 10,219.00 = 30,648.00 |
| Saldo actual del recibo | ✅ 30,648.00 − 10,219.00 = 20,429.00 |
| Cuota nº 9 = octubre | ✅ si la cuota 1 es febrero 2025 |
| Monto en letras | ✅ "DIEZ MIL DOSCIENTOS DIECINUEVE QUETZALES" |
| Fecha de pago vs. vencimiento | ⚠️ primera cuota el día 28; "otras condiciones" dicen "cada 30 del mes". Cuota de octubre pagada el 4 de noviembre, con mora Q 0.00 → correcto solo si el vencimiento es el 30 y se cuentan 5 días de gracia |
| Número de lote | ⚠️ en el contrato manuscrito se lee "36-834", en el recibo "36-B34" (probablemente B34) |

## Decisiones del usuario (2026-09-30)

- "FEL 2540" = número de factura emitida por SAT → campo **opcional** `numero_fel`, texto libre, sin relación ni validación.
- Plazo: **1 a 4 años**. Los montos del ejemplo no son reglas: todos los precios/montos los captura el usuario en el formulario; el sistema solo calcula derivados (total, saldo, plan de cuotas).

## Reglas de negocio derivadas

1. `total = precio_terreno + mejoras`; `saldo_a_pagar = total − enganche − otros_descuentos`.
2. Plan de cuotas generado por el sistema (sistema francés / cuota nivelada con la tasa pactada; con 0 % = división simple) y **última cuota ajustada** para cerrar el saldo exacto.
3. En cada recibo: `total = capital + intereses + recargo_mora + abono_capital + otros`; `saldo_actual = saldo_anterior − capital − abono_capital` (intereses y mora no reducen saldo).
4. Mora: si `fecha_pago > vencimiento + 5 días` → 5 % de la cuota por cada mes de atraso (el sistema lo **sugiere**; el cajero puede ajustar con motivo).
5. Abono a capital mínimo Q 2,000.00.
6. Desistimiento: penalidad = max(20 % del precio, 50 % de lo pagado).
7. Clientes existentes con pagos previos → carga de saldo/pagos históricos.
