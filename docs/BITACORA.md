# Bitácora de iteraciones

Una entrada por iteración, la más reciente al final. Formato:

```
## AAAA-MM-DD — título
- Cambios:
- Validación: (resultado de validar.py + pruebas manuales)
- Pendiente / riesgos:
```

## 2026-09-29 — Fase 0: cimientos del proyecto
- Cambios: creados `CLAUDE.md`; skills (`leer-pdf`, `generar-pdf`, `programacion`, `backend`, `sql`, `diseno-frontend`, `dominio-documentos`, `validar`, `nueva-funcionalidad`); agentes (`revisor-codigo`, `validador-qa`, `auditor-seguridad`); reglas por área en `.claude/rules/`; hooks post-edición y de inicio de sesión; `.claude/scripts/validar.py`; documentación en `docs/`.
- Validación: `validar.py` — docs OK; backend y frontend omitidos (aún no existen).
- Pendiente / riesgos: Node 18 debe actualizarse a 20+; git no instalado; PostgreSQL por instalar; preguntas abiertas en `REQUISITOS.md`.

## 2026-09-29 — Cambio de base de datos a MongoDB Atlas
- Cambios: ADR-002 (MongoDB Atlas + Beanie); skill `sql` → `mongodb`; regla `sql-migraciones` → `mongodb`; actualizados CLAUDE.md, backend skill, agentes, hook post-edición (patrones NoSQL), validar.py (sin alembic), settings.json, `.env.example`, ARQUITECTURA y ROADMAP. `MODELO-DATOS.md` reescrito como borrador centrado en clientes → contratos (promesa de compraventa) → pagos/recibos.
- Validación: validar.py (ver resultado en sesión).
- Pendiente / riesgos: leer el PDF real del usuario (`documentos-muestra/`) para fijar campos exactos; crear clúster Atlas.

## 2026-09-30 — Análisis del contrato y recibo reales
- Cambios: `docs/ANALISIS-DOCUMENTOS.md` (campos, validaciones, reglas; sin datos personales); `MODELO-DATOS.md` v2 con campos reales.
- Validación: aritmética de contrato y recibo cuadra; NIT y DPI válidos; detectadas inconsistencias (plazo 1 año vs 11 cuotas, día de pago 28 vs 30, lote 36-834 vs 36-B34, teléfonos distintos). Página 2 ilegible en parte.
- Pendiente / riesgos: respuestas del usuario a las preguntas; foto clara de condiciones generales; el usuario compartió la contraseña de Atlas en el chat → debe rotarla.

## 2026-09-30 — Fase 1: esqueleto del backend
- Cambios: `backend/.venv` (Python 3.13) con FastAPI 0.142, Beanie 2.2, PyMongo 4.18, ReportLab 5, pytest, ruff. Creados `app/core` (config desde `.env`, conexión Atlas, errores de dominio, correlativos atómicos, validación NIT/DPI, montos en letras), `app/modules/contratos/calculos.py` (totales + plan de cuotas con última cuota ajustada, 1–4 años), endpoint `/api/v1/salud`, `app/migrar.py` + `migraciones/0001_contadores.py`, `app/probar_conexion.py`. Hook post-edición: usa ruff del venv, ignora comentarios, salida ASCII-safe.
- Validación: `validar.py` → docs OK, ruff check OK, ruff format OK, pytest 49 pasan / 1 omitido (test de Atlas, sin `.env`). El plan de cuotas reproduce exactamente los saldos del recibo real (30,648.00 → 20,429.00, cuota 9 = octubre).
- Actualización: `.env` creado; conexión a Atlas OK (MongoDB 8.0.34); migración 0001 aplicada (colecciones `contadores`, `_migraciones`); test de Atlas pasa pero con fallo TLS intermitente (~1 de 3) en un nodo del clúster → IP pública cambiante no permitida en Network Access.
- Resolución: diagnóstico por nodo mostró alternancia exacta ok/fallo independiente de la versión TLS; la red del usuario sale por dos IPs públicas en round-robin y solo una estaba permitida. Agregadas ambas en Network Access → 24/24 handshakes, 6/6 `probar_conexion`, 3 corridas de pytest con 50/50. Si el proveedor cambia de IP reaparecerá `TLSV1_ALERT_INTERNAL_ERROR` → agregar la nueva IP.
- Pendiente / riesgos: rotar contraseña de Atlas;

## 2026-09-30 — Módulo de Promesas de Compra Venta (backend + PDF)
- Cambios: `core/{tipos,formato,ids}.py`; módulos `clientes`, `lotes`, `contratos` (schemas, modelos, service, router), `configuracion` (emisor + condiciones generales transcritas parcialmente, marcadas BORRADOR), `auditoria`; `pdf/{estilos,promesa}.py` (3 páginas: datos, condiciones generales, anexo plan de pagos). Crear promesa = transacción Atlas (cliente upsert por DPI, lote reservado, correlativo, auditoría). Tests de validación reemplazados con DPI/NIT ficticios (antes usaban datos reales). Hook post-edición ya no usa `ruff --fix` (borraba imports entre ediciones). `EmailStr` sustituido por patrón simple (sin dependencia extra).
- Validación: `validar.py` backend OK; pytest 75 pasan (incluye integración contra `facturas_test` en Atlas: crear, correlativo, conflicto de lote con rollback del correlativo, PDF + auditoría, 404, 422, anti-inyección, vista previa sin guardar). PDF revisado visualmente (página 1 cabe en una hoja). Servidor real: `/api/v1/salud` → conectada.
- Pendiente (ver entrada siguiente) / riesgos: **endpoints sin autenticación** (fase 2) → no exponer fuera de la máquina local; condiciones generales incompletas; representante legal vacío en configuración; un timeout de red aislado (WinError 121) en una corrida, no reproducido.

## 2026-09-30 — Recibos de caja, estado de cuenta y saldo inicial
- Decisión del usuario: clientes que ya venían pagando se cargan solo con su saldo actual.
- Cambios: `contratos`: `SaldoInicial` (cuotas pagadas + saldo; reprograma pendientes si el saldo difiere), `total_pagado_enganche`, cuotas con `capital_pagado`/`interes_pagado`. `calculos`: `plan_cuota_fija` (abono a capital acorta plazo sin cambiar cuota) y `mora_sugerida` (5 días de gracia, 5 % por mes o fracción). Nuevo módulo `recibos` (schemas, modelo, service transaccional, router): sugerencia de pago, registrar, listar/buscar, anular (solo el último, restaura snapshot `plan_anterior`), PDF de recibo (original + copia) y estado de cuenta PDF. Reglas del contrato aplicadas: cuotas en orden, abono mínimo Q 2,000 y solo estando al día, enganche no excede lo pactado, contrato cancelado → lote vendido. `app/ajustar_correlativo.py` ($max, nunca retrocede).
- Validación: `validar.py` OK; pytest 105 pasan (30 nuevos; integración Atlas reproduce el recibo real: cuota 9, octubre 2025, 30,648.00 → 20,429.00, mora 0 a los 5 días, 510.95 al sexto). PDFs revisados visualmente; corregido solapamiento No./FEL en el recibo.
- Pendiente / riesgos: sin autenticación; correlativos reales por ajustar; condiciones generales incompletas; frontend. siguiente: modelos Beanie de clientes/lotes/contratos/recibos y sus endpoints.

## 2026-10-01 — Condiciones generales leídas desde `textos.py`
- Problema: al editar `configuracion/textos.py` el PDF de la promesa seguía con el texto viejo, porque `obtener_configuracion()` había guardado una copia en la colección `configuracion` la primera vez.
- Cambios: `pdf/promesa.py` usa `CONDICIONES_GENERALES` de `textos.py`; quitado `condiciones_generales`/`Clausula` de `ConfiguracionDatos`; migración `0002_quitar_condiciones_de_configuracion` ($unset, con `revertir`). Corregido además un error de sintaxis (comillas sin cerrar) en la cláusula de limitaciones de uso.
- Validación: `validar.py --solo backend` OK (test nuevo `test_pdf_usa_el_texto_de_textos_py`); migración aplicada en Atlas; PDF del contrato 00002 descargado contiene el texto editado.
- Pendiente / riesgos: las condiciones no se guardan como instantánea por contrato → un PDF re-descargado de una promesa antigua sale con el texto actual.

## 2026-10-01 — Lotificación "Monaco", cuentas bancarias y corrección de `textos.py`
- Cambios: `textos.py` con las cláusulas editadas por el usuario (corregidas comillas sin cerrar en los incisos a/b y espacios entre frases; "CARGOS NO INCLUIDOS" queda sin texto y el PDF muestra solo el título). `ConfiguracionDatos.proyecto` = 'LOTIFICACIÓN "MONACO"'; nuevo `cuentas_bancarias` (Banrural ahorro 4269194666 y Banco Industrial ahorro 4516652, a nombre de Andrick Saul Estrada Aguilar), impreso en la página 1 de la promesa. Migración `0003_lotificacion_monaco_y_cuentas` (con `revertir`). Frontend: nombre en título y menú lateral.
- Validación: `validar.py` completo OK (8/8); tests nuevos de cuentas/proyecto y de cláusula sin texto; migración aplicada en Atlas; páginas 1 y 2 renderizadas y revisadas.
- Pendiente / riesgos: falta el texto de "CARGOS NO INCLUIDOS EN EL PRECIO DEL LOTE"; recibos y estado de cuenta también muestran el nuevo nombre del proyecto.

## 2026-10-01 — Datos del emisor: Inmobiliaria Estrada
- Cambios: `ConfiguracionDatos`: empresa "INMOBILIARIA ESTRADA", oficinas y proyecto "San Pedro Pinula, Jalapa, Kilómetro 124.5, Residenciales Monaco", tel. 5381-4009. Migración `0004_datos_inmobiliaria_estrada` (con `revertir`).
- Validación: pytest 108 OK, ruff OK; migración aplicada en Atlas; PDF del contrato 00003 descargado desde la API muestra el nuevo encabezado, la cláusula de arras y la razón notarial con Inmobiliaria Estrada.
- Pendiente / riesgos: `ciudad_documentos` sigue en "Jalapa".

## 2026-10-01 — Borrar promesas y recibos (borrado lógico)
- Cambios: `eliminado_en` + `motivo_eliminacion` en `Contrato` y `Recibo` (opcionales; los documentos existentes no necesitan migración porque `{eliminado_en: None}` también coincide con el campo ausente). `POST /contratos/{id}/eliminar` {motivo}: en una transacción borra la promesa y todos sus recibos y deja el lote `disponible` sin `contrato_id`. `POST /recibos/{id}/eliminar` {motivo}: un recibo vigente solo si es el último (revierte saldo/plan con la misma lógica que anular, extraída a `_revertir`); un recibo anulado se borra siempre. Listados, detalle, PDFs, estado de cuenta, sugerencia y registro de pagos ignoran lo borrado (404). Auditoría `eliminar`. Frontend: botón "Borrar promesa" en el detalle y "Borrar" en la tabla de recibos de la promesa, con `DialogoEliminar` (motivo validado con Zod `esquemaEliminar`).
- Validación: `validar.py` completo OK (8/8); 3 tests de integración nuevos (revertir/ocultar recibo, borrar anulado sin tocar saldos, borrar promesa libera lote y permite revenderlo) + test Zod.
- Pendiente / riesgos: sin autenticación, cualquiera con acceso a la API local puede borrar; cuando haya roles, limitar a administrador. No hay pantalla para restaurar lo borrado (los datos siguen en Atlas).

## 2026-10-15 — Lotificación "Tablon Campestre2"
- Cambios: `ConfiguracionDatos.proyecto` = 'LOTIFICACIÓN "TABLON CAMPESTRE2"'. Migración `0005_lotificacion_tablon_campestre2` (con `revertir` a "MONACO"). Frontend: nombre en título y menú lateral. Test de PDF actualizado.
- Validación: migración aplicada en Atlas; `validar.py`: ruff, lint, typecheck y build OK; pytest 110 OK + 1 error de red con Atlas (ConnectionReset) que pasó al repetirlo; vitest falló por timeout al arrancar workers con los servidores de desarrollo corriendo y pasó con `--pool=forks --maxWorkers=1` (48/48).
- Pendiente / riesgos: `direccion_oficinas` y `direccion_proyecto` siguen diciendo "Residenciales Monaco". Los PDFs leen la configuración actual, así que las promesas y recibos ya emitidos también salen con el nuevo nombre al re-descargarlos.

## 2026-10-19 — Elegir la lotificación en cada promesa
- Cambios: catálogo fijo `LOTIFICACIONES` (Monaco, Finca El Ensueño, Tablon Campestre2) en `lotes/schemas.py`. `ContratoCrear.lotificacion` obligatoria; se guarda en `Contrato`, se copia a cada `Recibo` y al `Lote`. PDFs de promesa (encabezado y cláusula de arras), recibo y estado de cuenta usan `nombre_lotificacion(...)`; las promesas anteriores (`null`) siguen usando `configuracion.proyecto`. El número de lote ahora es único por lotificación: índice (`lotificacion`, `codigo`) y migración `0006_lotes_por_lotificacion` que quita el índice `codigo_1` (con `revertir`). Frontend: selector obligatorio "Lotificación" (Zod) en la sección "Lotificación y firma"; se muestra en el detalle y en el listado; menú lateral y título dicen "Inmobiliaria Estrada".
- Validación: migración 0006 aplicada a `facturas_test`; `validar.py`: ruff, pytest, lint, typecheck y build OK; vitest falló otra vez por timeout al arrancar workers y pasó con `--maxWorkers=1` (50/50). Encabezado del PDF con "FINCA EL ENSUEÑO" renderizado a PNG y revisado (Ñ correcta).
- Migración 0006 aplicada en la base real (2026-10-20): `lotes` queda con índices `_id_`, `estado_1`, `lotificacion_1_codigo_1`.
- Migración `0007_lotificacion_existentes_tablon` aplicada en la base real (2026-10-20): todas las promesas (11), recibos (6) y lotes (10) anteriores pasan a `tablon_campestre2` (confirmado por el usuario); los ids modificados quedan en `_migracion_0007` para `revertir`. Verificado: 0 documentos sin lotificación, sin choques de número de lote.
- Decisión (usuario, 2026-10-20): `direccion_oficinas` y `direccion_proyecto` ("…Residenciales Monaco") son la misma para las 3 lotificaciones porque ahí está la oficina; no se cambian.

## 2026-10-20 — Obras de urbanización distintas para Monaco
- Cambios: `textos.py`: `VARIANTES` por lotificación + `condiciones_para(lotificacion, clausulas)`. Para `monaco`, en "OBRAS DE URBANIZACIÓN INCLUIDAS EN EL PRECIO DEL LOTE" el punto "2.Drenajes unicamente se permite Fosas Sépticas." pasa a "2.Red de distribución de drenaje."; el resto de la cláusula y las demás lotificaciones quedan igual. `pdf/promesa.py` aplica la variante según `contrato.lotificacion`.
- Validación: ruff OK; pytest 120 OK + 1 error de red con Atlas (sin primario, `ServerSelectionTimeoutError`) en `test_ids_inexistentes_o_mal_formados_404`, que pasó al repetir `test_contratos_api.py` (10/10). Test nuevo parametrizado por lotificación. Página 2 de una promesa Monaco renderizada a PNG y revisada.
- Decisión (usuario, 2026-10-20): todos los incisos de las demás cláusulas (incluido "LIMITACIONES EN EL USO DEL LOTE" d), que menciona fosas sépticas) quedan iguales también en Monaco.

## 2026-10-20 — Monaco: inciso d) de "Limitaciones en el uso del lote"
- Cambios: nueva variante en `textos.py` (`VARIANTES["monaco"]`): "d) Hacer uso adecuado del sistema de fosas septicas de aguas negras." → "d) Hacer uso adecuado del sistema de drenaje de aguas negras." Solo Monaco; las demás lotificaciones y los demás incisos quedan igual (reemplaza la decisión anterior de dejar este inciso igual).
- Validación: ruff OK; `test_pdf_promesa.py` 14/14 (test por lotificación ampliado); PDF de la promesa 00012 (Monaco) descargado del servidor en marcha tras la recarga y verificado.

## 2026-10-20 — Cobros y morosidad (cartera)
- Cambios: nuevo módulo `backend/app/modules/cartera/` (solo lectura, sin cambios al modelo de datos): `GET /api/v1/cartera?situacion=&buscar=&lotificacion=&fecha=` calcula al vuelo, para cada promesa vigente, la situación de pago (`moroso` = cuota vencida pasados los días de gracia; `en_gracia`; `por_vencer` = vence en ≤ 7 días; `al_dia`), próxima cuota (No., fecha, monto), día de pago mensual, cuotas vencidas, días de atraso, monto vencido, mora estimada (misma regla que `mora_sugerida`), enganche pendiente, último pago (recibos no anulados/eliminados) y `riesgo_rescision` (2+ cuotas en mora, cláusula del contrato). Resumen con conteos y totales; orden por atraso. `core/tipos.hoy_guatemala()` con UTC−6 fijo (Windows sin `tzdata`; Guatemala no tiene horario de verano). Frontend: pantalla `/cobros` ("Cobros y morosidad" en el menú) con tarjetas de resumen, filtros por situación (por defecto morosos), lotificación y búsqueda, teléfono con enlace `tel:` y botón "Registrar pago".
- Validación: `validar.py` 8/8 OK; `test_cartera.py` 9 tests (pura + Atlas `facturas_test`); 2 tests de pantalla nuevos; endpoint probado contra el servidor en marcha (4 promesas vigentes, todas al día al 20/10/2026).
- Pendiente / riesgos: muestra el teléfono completo en el listado (necesario para cobrar) — revisar enmascarado cuando haya roles; reporte PDF de morosos.

## 2026-10-20 — Reporte PDF de cobros y morosidad
- Cambios: `app/pdf/cartera.py` (carta horizontal): encabezado con fecha de corte, filtros, días de gracia y % de mora; tabla resumen (vigentes, morosos, en gracia, pagan esta semana, al día, riesgo de rescisión, monto vencido, mora estimada); tabla por cliente (nombre/promesa, teléfono, lote, día de pago y cuota, próxima cuota, cuotas vencidas, atraso, vencido, mora, total a cobrar, último pago) con fila de totales; filas con 2+ cuotas en mora sombreadas; leyenda "no válido como factura fiscal"; hora de generación en Guatemala. Endpoint `GET /api/v1/cartera/pdf` (mismos filtros que el listado, sin paginar) con auditoría `descargar_reporte_cobros` (sin datos personales). `service.cartera(..., tamano=None)` devuelve todo. Frontend: botón "Descargar reporte PDF" en `/cobros` que respeta la situación, búsqueda y lotificación seleccionadas.
- Validación: `validar.py` (ver resultado en sesión); `test_cartera.py` 12/12 (PDF con datos, PDF vacío, endpoint + auditoría); PDF real descargado del servidor en marcha (4 clientes al día) y revisado como imagen.
- Pendiente / riesgos: el teléfono aparece completo en el reporte (necesario para cobranza); revisar cuando existan roles.

## 2026-11-03 — Inicio de sesión exclusivo con Google + roles (ADR-003)
- Cambios: `app/core/seguridad.py` (verificación del ID token de Google con PyJWT contra las llaves públicas de Google: RS256, `aud`, `iss`, `exp`, `email_verified`; JWT de sesión HS256 en cookie `sesion` httpOnly + SameSite=Strict + path=/api; `usuario_actual`, `requiere_sesion` (rol consulta solo GET), `requiere_rol`; `sesion_version` para revocar sesiones; middleware `OrigenPermitido`; límite 10 intentos/min por IP). Módulo `usuarios` (colección nueva): `POST /auth/google`, `GET /auth/yo`, `POST /auth/salir`, `GET /auth/config`, `GET/POST/PATCH /usuarios` (solo admin; no auto-degradarse; siempre 1 admin). Clientes, contratos, recibos y cartera montados con `dependencies=[Depends(requiere_sesion)]`. `auditoria.usuario` = correo de la sesión (contextvar); índice TTL 90 días para `inicio_sesion_rechazado` (Beanie lo crea al arrancar). Config: `GOOGLE_CLIENT_ID`, `ADMIN_CORREOS`, `SESION_HORAS`, `COOKIE_SEGURA`, `ENTORNO` (produccion no arranca con secreto débil / cookie insegura / CORS http y oculta /docs). Dependencia nueva: `pyjwt[crypto]` (MIT). Frontend: `features/auth` (script oficial de Google Identity Services, `RequiereSesion` + contexto de usuario, pantalla de acceso, cierre de sesión y 401 global → vuelve al acceso), `features/usuarios` (pantalla `/usuarios` con formulario Zod), usuario y botón "Cerrar sesión" en el sidebar.
- Validación: `validar.py` 8/8 OK. `test_auth.py` 30/30 (tokens firmados con llave RSA local: válido, firma ajena, otra audiencia, otro emisor, expirado, correo sin verificar; 401 sin sesión/cookie falsificada; 429; flujo completo con Atlas; cuenta no autorizada 403 + auditoría; desactivación y cambio de rol revocan sesión; logout revoca cookies copiadas; google_sub distinto 403; consulta no puede POST; gestión de usuarios 201/403/404/409/422; Origin ajeno 403; producción insegura no arranca). Pantallas: acceso sin sesión, cerrar sesión, menú Usuarios solo admin, alta de usuario con validación. Agente `auditor-seguridad`: sin críticos; se corrigieron ALTO (secreto en producción) y los MEDIO de ADMIN_CORREOS, revocación, auditoría de rechazos y CSRF.
- Pendiente / riesgos: el usuario debe crear el OAuth Client ID en Google Cloud y llenar `GOOGLE_CLIENT_ID`, `ADMIN_CORREOS` y `JWT_SECRETO` en `.env`; no probado aún con Google real (requiere el Client ID). Pendientes de la auditoría: `nonce` en el ID token, atomicidad de la regla "último admin", `/salud` público.

## 2026-11-04 — Preparación del despliegue en Render
- Cambios: `render.yaml` (Blueprint): `facturas-api` (Python 3.13.7, `pip install . && python -m app.migrar` en el build, uvicorn con `--proxy-headers`, health check `/api/v1/salud`, `ENTORNO=produccion`, `COOKIE_SEGURA=true`, `JWT_SECRETO` generado por Render; secretos `sync: false`) y `facturas-web` (sitio estático, Node 22, `npm ci && npm run build`, reescritura `/api/*` → backend y `/*` → `index.html`, cabeceras X-Frame-Options/nosniff/Referrer-Policy). Mismo origen para el navegador → la cookie `SameSite=Strict` funciona sin CORS entre dominios; sin cambios de código. `docs/DESPLIEGUE.md` con el paso a paso (Git/GitHub, Atlas, Blueprint, Google OAuth, verificación). `.gitignore`: `*.egg-info/`.
- Validación: `app.main` importa con `ENTORNO=produccion`, cookie segura y CORS https; con CORS http se niega a arrancar (esperado). No se ha desplegado aún (falta Git/GitHub).
- Pendiente / riesgos: confirmar tras el primer deploy que la reescritura de Render reenvía `Set-Cookie` y `Origin` (paso 5 de la guía); si Render asigna otra URL al backend, corregir `destination` y `CORS_ORIGENES`. IP del limitador de login tomada de `X-Forwarded-For`. Atlas M0 sin backups automáticos.
