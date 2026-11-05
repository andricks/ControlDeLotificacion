# Roadmap

Marcar `[x]` al completar (solo con `/validar` en verde). Cada fase termina con una entrada en `BITACORA.md`.

## Fase 0 — Cimientos ✅
- [x] Skills, reglas, agentes, hooks y script de validación en `.claude/`
- [x] Documentación inicial (requisitos, arquitectura, modelo de datos)

## Fase 1 — Entorno y esqueleto
- [ ] Resolver preguntas abiertas de `REQUISITOS.md`
- [ ] Instalar git e inicializar repositorio
- [ ] Actualizar Node a 20 LTS o superior
- [x] Crear cuenta y clúster M0 en MongoDB Atlas
- [x] `MONGODB_URI` en `.env`; conexión verificada (MongoDB 8.0.34) y migración 0001 aplicada
- [x] Resolver fallo TLS intermitente: la red sale por 2 IPs públicas alternadas; ambas agregadas en Atlas Network Access
- [ ] Rotar contraseña de Atlas (fue compartida en el chat)
- [x] Leer y validar el PDF real de contrato + recibos → ajustar `MODELO-DATOS.md`
- [x] Esqueleto backend: FastAPI, config, conexión Beanie, errores, `/api/v1/salud`, pyproject con ruff/pytest
- [x] Runner de migraciones (`backend/migraciones/`) + migración 0001 de `contadores` (pendiente de aplicar en Atlas)
- [x] Lógica pura: validación NIT/DPI, montos en letras, totales y plan de cuotas (1–4 años) con tests
- [ ] Obtener texto claro de las condiciones generales (página 2 del contrato)
- [ ] Esqueleto frontend: Vite + React + TS + Tailwind + Router + Query; scripts lint/typecheck/test/build
- [ ] `validar.py` en verde con ambos esqueletos

## Fase 1b — Promesas de compra-venta (backend) ✅
- [x] Modelos Beanie: clientes, lotes, contratos, configuración del emisor, auditoría
- [x] `POST /contratos` (transacción: cliente por DPI + reserva de lote + correlativo + auditoría)
- [x] `POST /contratos/calcular` (vista previa sin guardar), `GET /contratos` (búsqueda), `GET /contratos/{id}`
- [x] `GET /contratos/{id}/pdf` — Promesa de Compra Venta (datos + condiciones generales + anexo plan de pagos)
- [x] `GET /clientes`, `/clientes/{id}`, `/clientes/por-dpi/{dpi}` (autocompletar)
- [ ] Completar/validar texto de condiciones generales y datos del representante legal

## Fase 1c — Recibos de caja (backend) ✅
- [x] Registrar recibo (transacción: correlativo, desglose, saldos, plan de cuotas, auditoría); mora sugerida
- [x] PDF del Recibo de Caja (original + copia); estado de cuenta del contrato en PDF
- [x] Anulación del último recibo con motivo (revierte saldo, plan y estado exactos)
- [x] Clientes del papel: `saldo_inicial` en la promesa (solo saldo actual, decisión del usuario)
- [x] `python -m app.ajustar_correlativo recibo|contrato <último usado>` para continuar la numeración
- [ ] Ajustar correlativos reales en Atlas (el usuario debe indicar últimos números usados)

## Fase 1d — Frontend (formularios y descargas)
- [ ] Actualizar Node a 20 LTS+ y crear proyecto Vite + React + TS + Tailwind
- [ ] Formulario "Nueva promesa" con vista previa del plan y autocompletar por DPI
- [ ] Formulario "Registrar pago" con sugerencia de cuota/mora
- [ ] Listados de promesas y recibos con botones de descarga PDF

## Fase 1e — Cobros y morosidad
- [x] `GET /cartera`: situación de pago por promesa vigente (moroso / en gracia / por vencer / al día), próxima cuota, día de pago, cuotas vencidas, monto vencido, mora estimada, último pago, riesgo de rescisión (2+ cuotas)
- [x] Pantalla "Cobros y morosidad" (`/cobros`) con resumen, filtros por situación/lotificación y búsqueda
- [x] Reporte PDF de cobros (`GET /cartera/pdf`, mismos filtros; por defecto morosos) con botón en `/cobros`

## Fase 2 — Autenticación y base
- [x] Login **exclusivo con Google** (ADR-003): verificación del ID token, lista blanca `usuarios` + `ADMIN_CORREOS`, sesión en cookie httpOnly, roles admin/operador/consulta, todas las rutas de negocio protegidas
- [x] Frontend: pantalla de acceso con botón de Google, `RequiereSesion`, usuario y "Cerrar sesión" en el sidebar, pantalla `/usuarios` (solo admin)
- [x] Configurar `GOOGLE_CLIENT_ID`, `ADMIN_CORREOS` y un `JWT_SECRETO` fuerte en `.env`
- [x] Probar el acceso real con Google en el navegador (2026-11-04, confirmado por el usuario)
- [ ] Ajustes que el usuario observó en las pruebas (pendiente de que los detalle)
- [x] Auditoría transversal: `auditoria.usuario` = correo de la sesión
- [ ] CRUD de partes con validación NIT/DPI

## Fase 3 — Archivos y PDF
- [ ] Almacenamiento seguro + subida con validación + deduplicación
- [ ] Extracción de texto/metadatos (`pdf/lectura.py`) + miniaturas
- [ ] Plantillas base de PDF (estilos, encabezado, pie) + visor en frontend

## Fase 4 — Terrenos y planos
- [ ] CRUD terrenos (finca/folio/libro, área con conversión)
- [ ] CRUD planos con versionado y colindancias; ficha técnica PDF

## Fase 5 — Contratos
- [ ] CRUD contratos con partes y roles; alertas por vencer; PDF de contrato

## Fase 6 — Facturas
- [ ] CRUD facturas con líneas, IVA, estados; sugerencias desde PDF FEL; PDF de factura

## Fase 7 — Búsqueda, expedientes y reportes
- [ ] Búsqueda global (texto completo en PDFs)
- [ ] Expediente PDF unido por terreno/contrato
- [ ] Descarga masiva ZIP
- [ ] Reportes PDF y dashboard

## Fase 8 — Endurecimiento y despliegue
- [ ] Auditoría de seguridad completa (agente `auditor-seguridad`)
- [ ] Respaldo/restauración documentados y probados
- [ ] Despliegue
