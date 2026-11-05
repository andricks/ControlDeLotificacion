---
paths:
  - "backend/**/*.py"
---

# Reglas: backend Python

- Capas: `router → service → repository → models`. El router no importa `select` ni usa la sesión directamente.
- Dinero y cantidades: `Decimal` con `quantize(Decimal("0.01"), ROUND_HALF_UP)`. Prohibido `float`.
- Totales, IVA y estados los calcula el servidor; nunca se aceptan del cliente.
- Configuración solo vía `app/core/config.py` (`Settings`); nada de `os.environ[...]` disperso ni valores hardcodeados.
- Excepciones de dominio de `app/core/errores.py`; nada de `HTTPException` dentro de services.
- Cada endpoint: dependencia de usuario/rol, `response_model`, `summary` en español, y tests (2xx, 401, 403, 404, 422).
- Crear/editar/anular/eliminar/descargar → `auditoria.registrar(...)`.
- Borrado de documentos legales = lógico (`eliminado_en`).
- `logging` en lugar de `print`; no loguear datos personales ni contenido de documentos.
- Type hints en funciones públicas; `ruff check` y `ruff format` limpios.
