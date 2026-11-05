---
name: nueva-funcionalidad
description: Flujo guiado para implementar una funcionalidad nueva de punta a punta (especificación → modelo/migración → servicio → API → tests → UI → PDF → validación → documentación). Usar cuando el usuario pida una funcionalidad nueva o escriba /nueva-funcionalidad <descripción>.
argument-hint: "<descripción de la funcionalidad>"
disable-model-invocation: true
---

# /nueva-funcionalidad $ARGUMENTS

## Fase 1 — Especificar (no escribir código todavía)

1. Leer `docs/REQUISITOS.md`, `docs/MODELO-DATOS.md`, `docs/ROADMAP.md` y la skill `dominio-documentos`.
2. Copiar `docs/plantillas/PLANTILLA-FUNCIONALIDAD.md` a `docs/funcionalidades/<nnn>-<nombre-corto>.md` y completarla: objetivo, historias de usuario, criterios de aceptación verificables, cambios de datos, endpoints, pantallas, PDFs, permisos, casos borde.
3. Si hay ambigüedades de negocio, **preguntar al usuario** antes de seguir. Mostrar un resumen de la especificación y esperar aprobación.

## Fase 2 — Implementar en capas (validando cada capa)

| Paso | Skill | Validación al terminar el paso |
|---|---|---|
| 1. Modelo + índices (+ script de migración si toca datos existentes) | `mongodb` | tests del modelo contra `facturas_test`; `python -m app.migrar` idempotente |
| 2. Schemas + repository + service | `backend` | tests unitarios del service (`pytest tests/<modulo>`) |
| 3. Router / endpoints | `backend` | tests de API (2xx, 401, 403, 404, 422) |
| 4. PDF (si aplica) | `generar-pdf` / `leer-pdf` | test que el PDF inicia con `%PDF-` y contiene los datos clave |
| 5. UI | `diseno-frontend` | `npm run typecheck && npm run test`, revisión visual |

Después de cada paso: `python .claude/scripts/validar.py --rapido`. No avanzar con fallos.

## Fase 3 — Cerrar

1. `/validar` completo.
2. Para cambios grandes, lanzar en paralelo los agentes `revisor-codigo`, `validador-qa` y (si toca auth, archivos o datos sensibles) `auditor-seguridad`. Corregir hallazgos confirmados.
3. Marcar criterios de aceptación cumplidos en el archivo de la funcionalidad.
4. Actualizar `docs/ROADMAP.md`, `docs/MODELO-DATOS.md` y añadir entrada en `docs/BITACORA.md`.
5. Resumen final al usuario: qué se hizo, cómo probarlo, qué queda pendiente.
