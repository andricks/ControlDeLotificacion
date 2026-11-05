# Reglas: seguridad (siempre aplican)

- Secretos solo en `.env` (no versionado). Mantener `.env.example` con claves sin valores reales.
- No leer ni imprimir el contenido de `.env` en la conversación.
- Datos personales (DPI, direcciones, teléfonos) y documentos: acceso por rol, enmascarado en listados, fuera de logs.
- Toda descarga y toda modificación de documentos queda en la tabla `auditoria`.
- No instalar dependencias nuevas sin mencionarlo y justificarlo; preferir librerías mantenidas y con licencia permisiva (evitar AGPL como PyMuPDF).
- No ejecutar comandos destructivos (`Remove-Item -Recurse`, `drop()`/`delete_many({})` en Atlas, borrar colecciones, borrar `storage/`) sin confirmación explícita del usuario.
