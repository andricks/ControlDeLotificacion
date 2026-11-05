# Sistema de Gestión Documental — Facturas, Contratos y Planos de Terrenos

Sistema web para **registrar, organizar, buscar y descargar en PDF** facturas, contratos y planos de terrenos (contexto Guatemala: NIT, DPI, IVA 12 %, quetzales, finca/folio/libro).

> Estado actual: **Promesas de Compra Venta, Recibos de Caja y Cobros (backend + frontend, con PDFs); acceso exclusivo con cuenta de Google y roles** (ver `docs/ROADMAP.md`, `docs/decisiones/ADR-003-login-google.md`). Todo endpoint nuevo de negocio debe montarse con `dependencies=[Depends(requiere_sesion)]` y probarse con las fixtures `api` / `cliente_con_rol`. Caso de negocio real: promesas de compra-venta de lotes y recibos de caja — ver `docs/ANALISIS-DOCUMENTOS.md`.

## Documentos clave (leer antes de implementar)

| Documento | Para qué |
|---|---|
| `docs/REQUISITOS.md` | Qué debe hacer el sistema (funcionales y no funcionales) |
| `docs/ARQUITECTURA.md` | Capas, carpetas, flujo de datos, almacenamiento de archivos |
| `docs/MODELO-DATOS.md` | Tablas, relaciones y reglas de negocio de datos |
| `docs/ROADMAP.md` | Fases e hitos; marca aquí lo terminado |
| `docs/BITACORA.md` | Registro de cada iteración (qué se hizo, cómo se validó) |
| `docs/decisiones/` | ADRs: decisiones técnicas y por qué |
| `docs/plantillas/` | Plantilla de especificación de funcionalidad |

## Stack (ver `docs/decisiones/ADR-001-stack.md`)

- **Backend:** Python 3.12+ · FastAPI · Beanie 2.x (ODM sobre PyMongo async) · Pydantic v2 · pytest · ruff
- **Base de datos:** **MongoDB Atlas** (ver `docs/decisiones/ADR-002-mongodb-atlas.md`); tests contra una base `facturas_test` desechable
- **PDF:** pdfplumber (leer texto/tablas) · pypdf (unir/dividir/metadatos) · pypdfium2 (miniaturas) · ReportLab (generar) · pytesseract (OCR opcional)
- **Frontend:** React 18 · Vite · TypeScript estricto · Tailwind CSS · React Router · TanStack Query · React Hook Form + Zod · Vitest
- **Node:** requiere 20 LTS o superior (la máquina tiene 18.16 → actualizar antes de crear el frontend)

## Estructura objetivo

```
backend/app/{core,modules/<dominio>,pdf}   backend/migraciones   backend/tests
frontend/src/{api,components,features/<dominio>,pages,lib}
storage/          ← archivos subidos y PDFs generados (NUNCA en git)
docs/             ← documentación viva
.claude/          ← skills, reglas, agentes, hooks, scripts de validación
```

## Comandos

```powershell
# Validación completa (usar SIEMPRE antes de dar una tarea por terminada)
python .claude/scripts/validar.py
python .claude/scripts/validar.py --solo backend      # o frontend
python .claude/scripts/validar.py --rapido            # sin build ni tests lentos

# Backend (desde backend/)
.venv\Scripts\activate ; uvicorn app.main:app --reload
pytest ; ruff check . ; ruff format .
python -m app.migrar            # aplica scripts pendientes de backend/migraciones/

# Frontend (desde frontend/)
npm run dev ; npm run lint ; npm run typecheck ; npm run test ; npm run build

# Extraer contenido de un PDF (skill leer-pdf)
python .claude/skills/leer-pdf/scripts/extraer_pdf.py ruta.pdf --json
```

## Flujo de trabajo obligatorio (iterar y validar)

1. **Entender:** leer la sección relevante de `docs/` y la skill del área (`backend`, `mongodb`, `diseno-frontend`, `generar-pdf`, `leer-pdf`, `dominio-documentos`).
2. **Especificar:** para funcionalidades nuevas usar `/nueva-funcionalidad` (crea spec desde `docs/plantillas/PLANTILLA-FUNCIONALIDAD.md`).
3. **Implementar en pasos pequeños:** modelo/índices → servicio → endpoint → tests → UI.
4. **Validar:** `/validar` (ejecuta `.claude/scripts/validar.py` + checklist). No declarar "listo" con validaciones fallando; reportar fallos tal cual.
5. **Revisar:** para cambios grandes, usar los agentes `revisor-codigo`, `validador-qa` y `auditor-seguridad`.
6. **Registrar:** añadir entrada en `docs/BITACORA.md` y actualizar `docs/ROADMAP.md` / `docs/MODELO-DATOS.md` si cambió algo.

## Reglas no negociables

- Idioma: código (identificadores) en **español sin tildes** para el dominio (`factura`, `numero_serie`), inglés solo para términos técnicos de framework. Mensajes al usuario en español.
- Dinero: `Decimal` en Python / `Decimal128` en MongoDB. **Nunca `float`.** Moneda por defecto `GTQ`.
- Fechas: guardar en UTC, mostrar en `America/Guatemala`.
- Operaciones que modifican varios documentos (p. ej. registrar pago + actualizar saldo) van en **transacción**.
- Correlativos (número de contrato/recibo) con contador atómico, nunca `count()+1`.
- Cambios sobre datos existentes pasan por un **script en `backend/migraciones/`**; nunca editar la BD a mano en Atlas.
- La cadena de conexión de Atlas (`MONGODB_URI`) solo en `.env`.
- Archivos: validar tipo real (magic bytes), tamaño máximo, calcular SHA-256, guardar fuera del webroot, nombre interno UUID.
- Secretos solo en `.env` (no se versiona; existe `.env.example`).
- Toda descarga PDF debe verificar permisos del usuario y quedar en la tabla `auditoria`.
- Ningún endpoint sin tests; ningún componente de formulario sin validación Zod.
- El sistema **registra** facturas; no certifica FEL ante SAT (eso requiere un certificador autorizado — ver skill `dominio-documentos`).

Las reglas detalladas por área están en `.claude/rules/` (se cargan según los archivos que se editen).
