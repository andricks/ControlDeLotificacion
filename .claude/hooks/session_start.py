"""Hook SessionStart: recuerda a Claude en qué punto va el proyecto.

Inyecta la fase actual del ROADMAP y la última entrada de la BITACORA
para que cada sesión continúe la iteración donde quedó la anterior.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def leer(ruta: Path) -> str:
    try:
        return ruta.read_text(encoding="utf-8")
    except OSError:
        return ""


def main() -> None:
    roadmap = leer(RAIZ / "docs" / "ROADMAP.md")
    bitacora = leer(RAIZ / "docs" / "BITACORA.md")

    pendientes = [l.strip() for l in roadmap.splitlines() if l.strip().startswith("- [ ]")][:6]
    entradas = re.split(r"\n(?=## )", bitacora)
    ultima = entradas[-1].strip() if len(entradas) > 1 else "(sin entradas todavía)"

    contexto = (
        "Estado del proyecto (auto-generado al iniciar sesión):\n"
        "Próximas tareas del ROADMAP:\n" + ("\n".join(pendientes) or "(ninguna)") +
        "\n\nÚltima entrada de BITACORA:\n" + ultima[:1500] +
        "\n\nRecuerda: validar con `python .claude/scripts/validar.py` y registrar en docs/BITACORA.md."
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": contexto}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
