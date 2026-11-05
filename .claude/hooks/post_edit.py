"""Hook PostToolUse (Write|Edit): valida el archivo recién editado.

- Nunca bloquea: siempre termina con código 0.
- Si encuentra problemas, los devuelve a Claude como `additionalContext`
  para que los corrija en la siguiente iteración.
- Si la herramienta (ruff, eslint...) aún no está instalada, se omite en silencio.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# Patrones sospechosos de secretos o malas prácticas del proyecto.
PATRONES_PROHIBIDOS = [
    (re.compile(r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]{6,}['\"]", re.I),
     "Posible secreto en código: muévelo a .env / settings."),
    (re.compile(r"\bfloat\s*\(.*(monto|total|precio|iva|subtotal)", re.I),
     "Uso de float con dinero: usa Decimal."),
    (re.compile(r"(monto|total|precio|iva|subtotal)\w*\s*:\s*float\b", re.I),
     "Campo monetario tipado como float: usa Decimal / Decimal128."),
    (re.compile(r"[\"']\$(where|function)[\"']"),
     "$where/$function en MongoDB: prohibido (ejecuta JavaScript, riesgo de inyección)."),
    (re.compile(r"\.(find|find_one|find_many|delete_many|update_many)\(\s*(request|body|payload|datos_cliente)\b"),
     "Filtro de MongoDB con datos crudos del cliente: construye el filtro desde un schema validado."),
    (re.compile(r"count(_documents)?\(.*\)\s*\+\s*1"),
     "Correlativo con count()+1: usa el contador atómico ($inc en 'contadores')."),
    (re.compile(r"dangerouslySetInnerHTML"),
     "dangerouslySetInnerHTML: evitar salvo sanitización explícita."),
]


def ejecutar(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           timeout=50, encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 0, f"(omitido: {e})"


def revisar_python(ruta: Path) -> list[str]:
    problemas: list[str] = []
    ruff_venv = RAIZ / "backend" / ".venv" / "Scripts" / "ruff.exe"
    ruff = str(ruff_venv) if ruff_venv.exists() else shutil.which("ruff")
    if not ruff:
        return problemas
    cwd = RAIZ / "backend" if (RAIZ / "backend").exists() else RAIZ
    ejecutar([ruff, "format", str(ruta)], cwd)
    # Sin --fix: autocorregir borra imports "no usados" entre ediciones de varios pasos.
    code, out = ejecutar([ruff, "check", str(ruta)], cwd)
    if code != 0 and out:
        problemas.append(f"ruff check:\n{out[:3000]}")
    return problemas


def revisar_ts(ruta: Path) -> list[str]:
    frontend = RAIZ / "frontend"
    eslint = frontend / "node_modules" / ".bin" / "eslint.cmd"
    if not eslint.exists():
        return []
    code, out = ejecutar([str(eslint), "--fix", str(ruta)], frontend)
    return [f"eslint:\n{out[:3000]}"] if code != 0 and out else []


def revisar_patrones(ruta: Path) -> list[str]:
    try:
        texto = ruta.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    avisos = []
    for patron, mensaje in PATRONES_PROHIBIDOS:
        for n, linea in enumerate(texto.splitlines(), 1):
            limpia = linea.strip()
            if limpia.startswith(("#", "//", "*", '"""', "'''")):
                continue  # comentarios y docstrings de una línea no son código
            if patron.search(linea):
                avisos.append(f"{ruta.name}:{n}: {mensaje}")
                break
    return avisos


def main() -> None:
    try:
        # utf-8-sig: PowerShell puede anteponer un BOM al stdin.
        datos = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    except (json.JSONDecodeError, ValueError):
        return
    entrada = datos.get("tool_input") or {}
    respuesta = datos.get("tool_response") or {}
    ruta_txt = entrada.get("file_path") or respuesta.get("filePath")
    if not ruta_txt:
        return
    ruta = Path(ruta_txt)
    if not ruta.exists() or ".claude" in ruta.parts:
        return

    problemas: list[str] = []
    sufijo = ruta.suffix.lower()
    if sufijo == ".py":
        problemas += revisar_python(ruta)
    elif sufijo in {".ts", ".tsx", ".js", ".jsx"}:
        problemas += revisar_ts(ruta)
    if sufijo in {".py", ".ts", ".tsx", ".js", ".jsx", ".sql"}:
        problemas += revisar_patrones(ruta)

    if problemas:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "Validación automática encontró problemas en "
                f"{ruta.name}. Corrígelos:\n" + "\n".join(problemas),
            }
        }))  # ensure_ascii (default) evita tildes corruptas en la consola de Windows


if __name__ == "__main__":
    try:
        main()
    except Exception:  # un hook nunca debe romper la sesión
        pass
    sys.exit(0)
