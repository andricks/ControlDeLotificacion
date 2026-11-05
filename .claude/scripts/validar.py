"""Validador integral del proyecto.

Uso:
    python .claude/scripts/validar.py                 # todo
    python .claude/scripts/validar.py --solo backend  # backend | frontend | docs
    python .claude/scripts/validar.py --rapido        # omite build y tests marcados 'lento'

Cada etapa se OMITE (no falla) si su parte del proyecto todavía no existe,
así el script sirve desde la fase 0 hasta producción.
Código de salida: 0 = todo OK, 1 = alguna verificación falló.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BACKEND = RAIZ / "backend"
FRONTEND = RAIZ / "frontend"
ES_WINDOWS = os.name == "nt"


@dataclass
class Resultado:
    etapa: str
    estado: str  # OK | FALLO | OMITIDO
    detalle: str = ""
    segundos: float = 0.0


def python_backend() -> str | None:
    venv = BACKEND / ".venv" / ("Scripts/python.exe" if ES_WINDOWS else "bin/python")
    return str(venv) if venv.exists() else shutil.which("python")


def correr(etapa: str, cmd: list[str], cwd: Path) -> Resultado:
    inicio = time.time()
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900,
                           shell=ES_WINDOWS and cmd[0] in {"npm", "npx"})
    except (OSError, subprocess.TimeoutExpired) as e:
        return Resultado(etapa, "FALLO", str(e), time.time() - inicio)
    salida = (r.stdout + "\n" + r.stderr).strip()
    estado = "OK" if r.returncode == 0 else "FALLO"
    detalle = "" if estado == "OK" else "\n".join(salida.splitlines()[-40:])
    return Resultado(etapa, estado, detalle, time.time() - inicio)


def tiene_modulo(py: str, modulo: str) -> bool:
    r = subprocess.run([py, "-c", f"import {modulo}"], capture_output=True)
    return r.returncode == 0


def validar_backend(rapido: bool) -> list[Resultado]:
    if not (BACKEND / "app").exists():
        return [Resultado("backend", "OMITIDO", "backend/app no existe todavía")]
    py = python_backend()
    res: list[Resultado] = []
    if py and tiene_modulo(py, "ruff"):
        res.append(correr("backend: ruff check", [py, "-m", "ruff", "check", "."], BACKEND))
        res.append(correr("backend: ruff format", [py, "-m", "ruff", "format", "--check", "."], BACKEND))
    else:
        res.append(Resultado("backend: ruff", "OMITIDO", "ruff no instalado"))
    if py and tiene_modulo(py, "mypy") and (BACKEND / "pyproject.toml").exists():
        res.append(correr("backend: mypy", [py, "-m", "mypy", "app"], BACKEND))
    if py and tiene_modulo(py, "pytest"):
        cmd = [py, "-m", "pytest", "-q"]
        if rapido:
            cmd += ["-m", "not lento"]
        res.append(correr("backend: pytest", cmd, BACKEND))
    else:
        res.append(Resultado("backend: pytest", "OMITIDO", "pytest no instalado"))
    return res


def validar_frontend(rapido: bool) -> list[Resultado]:
    if not (FRONTEND / "package.json").exists():
        return [Resultado("frontend", "OMITIDO", "frontend/package.json no existe todavía")]
    if not (FRONTEND / "node_modules").exists():
        return [Resultado("frontend", "FALLO", "Falta node_modules: ejecuta `npm install` en frontend/")]
    import json
    scripts = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8")).get("scripts", {})
    res: list[Resultado] = []
    etapas = ["lint", "typecheck", "test"] + ([] if rapido else ["build"])
    for s in etapas:
        if s not in scripts:
            res.append(Resultado(f"frontend: {s}", "OMITIDO", f"script '{s}' no definido en package.json"))
            continue
        cmd = ["npm", "run", s] + (["--", "--run"] if s == "test" else [])
        res.append(correr(f"frontend: {s}", cmd, FRONTEND))
    return res


def validar_docs() -> list[Resultado]:
    requeridos = ["CLAUDE.md", "docs/REQUISITOS.md", "docs/ARQUITECTURA.md",
                  "docs/MODELO-DATOS.md", "docs/ROADMAP.md", "docs/BITACORA.md"]
    faltan = [p for p in requeridos if not (RAIZ / p).exists()]
    res = [Resultado("docs: archivos base", "FALLO" if faltan else "OK",
                     "Faltan: " + ", ".join(faltan) if faltan else "")]
    for secreto in [".env", "backend/.env", "frontend/.env"]:
        if (RAIZ / secreto).exists() and (RAIZ / ".gitignore").exists():
            gi = (RAIZ / ".gitignore").read_text(encoding="utf-8")
            if ".env" not in gi:
                res.append(Resultado("seguridad: .gitignore", "FALLO", ".env no está en .gitignore"))
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", choices=["backend", "frontend", "docs"])
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()

    resultados: list[Resultado] = []
    if args.solo in (None, "docs"):
        resultados += validar_docs()
    if args.solo in (None, "backend"):
        resultados += validar_backend(args.rapido)
    if args.solo in (None, "frontend"):
        resultados += validar_frontend(args.rapido)

    iconos = {"OK": "[OK]    ", "FALLO": "[FALLO] ", "OMITIDO": "[--]    "}
    print("\n=== RESUMEN DE VALIDACIÓN ===")
    for r in resultados:
        extra = f" ({r.segundos:.1f}s)" if r.segundos else ""
        nota = f" — {r.detalle}" if r.estado == "OMITIDO" else ""
        print(f"{iconos[r.estado]}{r.etapa}{extra}{nota}")
    fallos = [r for r in resultados if r.estado == "FALLO"]
    for r in fallos:
        print(f"\n--- Detalle: {r.etapa} ---\n{r.detalle}")
    print(f"\nTotal: {len(resultados)} | OK: {sum(r.estado == 'OK' for r in resultados)} "
          f"| Fallos: {len(fallos)} | Omitidos: {sum(r.estado == 'OMITIDO' for r in resultados)}")
    return 1 if fallos else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
