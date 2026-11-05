---
name: validar
description: Ejecuta la validación completa del proyecto (lint, formato, tipos, tests, build, migraciones, docs) y revisa la checklist de calidad. Usar al terminar cualquier implementación, antes de declarar una tarea completa, o cuando el usuario escriba /validar.
argument-hint: "[backend|frontend|docs] [--rapido]"
---

# /validar — ciclo de validación

1. Ejecutar:
   ```powershell
   python .claude/scripts/validar.py $ARGUMENTS
   ```
   (si el argumento es `backend`, `frontend` o `docs`, pasarlo como `--solo <valor>`).

2. Si hay **FALLOS**:
   - Leer el detalle, corregir la causa raíz (no silenciar reglas de lint ni saltar tests).
   - Volver a ejecutar. Máximo 3 ciclos de corrección automática; si persiste, detenerse y explicar al usuario qué falla y por qué.

3. Revisar manualmente lo que el script no puede comprobar, según lo que se haya cambiado:
   - [ ] ¿Los totales/IVA se calculan en el servidor con `Decimal`?
   - [ ] ¿Cada endpoint nuevo verifica permisos y tiene tests de 401/403/404/422?
   - [ ] ¿Las descargas PDF registran auditoría y ponen `Content-Disposition` correcto?
   - [ ] ¿Los cambios de modelo tienen índices y, si afectan datos existentes, script en `backend/migraciones/`?
   - [ ] ¿Las operaciones multi-documento usan transacción y los correlativos el contador atómico?
   - [ ] ¿La UI tiene estados cargando / vacío / error?
   - [ ] ¿Se actualizaron `docs/MODELO-DATOS.md` y `docs/ROADMAP.md` si aplica?

4. Registrar en `docs/BITACORA.md` una entrada:
   ```
   ## AAAA-MM-DD — <título corto>
   - Cambios: ...
   - Validación: <resumen de validar.py: OK/Fallos/Omitidos> + pruebas manuales
   - Pendiente / riesgos: ...
   ```

5. Informar al usuario el resultado **tal cual** (qué pasó, qué falló, qué se omitió y por qué). Etapas "OMITIDO" no cuentan como validadas.
