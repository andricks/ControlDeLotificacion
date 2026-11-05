---
name: programacion
description: Estándares generales de programación del proyecto — nombres, estructura, manejo de errores, tests, commits y cómo trabajar en pasos pequeños verificables. Usar al escribir o refactorizar cualquier código (Python o TypeScript) de este proyecto.
---

# Estándares de programación

## Principios

1. **Pasos pequeños y verificables.** Cada cambio debe poder validarse con `python .claude/scripts/validar.py`. Si un cambio toca más de ~5 archivos, dividirlo.
2. **Primero el test del comportamiento**, luego la implementación (al menos para reglas de negocio: cálculos de IVA, estados, permisos).
3. **Sin código muerto ni "por si acaso".** Nada de funcionalidades no pedidas.
4. **Legible > ingenioso.** Funciones cortas (< 40 líneas), un nivel de abstracción por función.
5. **Fallar temprano y con mensaje claro** en español para el usuario, técnico en logs.

## Nombres

| Elemento | Python | TypeScript |
|---|---|---|
| Variables / funciones | `snake_case`: `calcular_iva` | `camelCase`: `calcularIva` |
| Clases / tipos / componentes | `PascalCase`: `FacturaCrear` | `PascalCase`: `FacturaFormulario` |
| Constantes | `MAYUSCULAS`: `TASA_IVA` | `MAYUSCULAS` |
| Archivos | `snake_case.py` | componentes `PascalCase.tsx`, resto `camelCase.ts` |
| Colecciones / campos MongoDB | `snake_case`, colecciones en plural: `contratos`, `pagos` | — |

Dominio en español **sin tildes ni ñ** en identificadores (`anio`, `numero`, `tamano`). Términos técnicos del framework se quedan en inglés (`router`, `schema`, `hook`).

## Manejo de errores

- Backend: excepciones de dominio propias (`NoEncontrado`, `ReglaNegocio`, `SinPermiso`) en `app/core/errores.py`, traducidas a HTTP en un único handler. Nunca `except Exception: pass`.
- Respuesta de error estándar: `{"detalle": "mensaje para el usuario", "codigo": "FACTURA_DUPLICADA", "campos": {...}}`.
- Frontend: los errores de la API se muestran con toast/alert; errores de campo se pintan en el formulario.
- Logs con `logging` (nunca `print` en código de app); nunca loguear contraseñas, tokens ni contenido de documentos.

## Tests

- Python: `pytest`, un archivo por módulo `tests/<modulo>/test_<archivo>.py`. Fixtures en `conftest.py`. Factories para datos de prueba.
- Nombre descriptivo: `test_no_permite_factura_con_total_negativo`.
- Cubrir: caso feliz, validaciones, permisos (403), no encontrado (404), duplicados (409).
- Tests lentos (OCR, PDFs grandes) marcados `@pytest.mark.lento`.
- Frontend: Vitest + Testing Library; probar comportamiento visible, no detalles internos.

## Tipado

- Python: type hints en todas las funciones públicas; Pydantic para bordes (entrada/salida HTTP).
- TypeScript: `strict: true`, prohibido `any` (usar `unknown` + validación Zod). Tipos de API generados o definidos en `src/api/tipos.ts`.

## Control de versiones (cuando se instale git)

- Ramas: `feat/facturas-crud`, `fix/iva-redondeo`, `docs/modelo-datos`.
- Commits convencionales en español: `feat(facturas): crear endpoint de descarga PDF`.
- Nunca commitear `.env`, `storage/`, `node_modules/`, `.venv/`.

## Checklist antes de decir "terminado"

- [ ] `python .claude/scripts/validar.py` sin fallos (o fallos reportados explícitamente)
- [ ] Tests nuevos para el comportamiento nuevo
- [ ] Docs actualizadas (`MODELO-DATOS.md` si cambió el esquema, `BITACORA.md` siempre)
- [ ] Sin secretos, sin `print`, sin `console.log` olvidados, sin TODO sin ticket
