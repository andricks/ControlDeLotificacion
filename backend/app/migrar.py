"""Runner de migraciones de datos para MongoDB.

Cada archivo `migraciones/NNNN_descripcion.py` define `async def aplicar(db)` y
`async def revertir(db)`. Las aplicadas se registran en la colección `_migraciones`.

Uso (desde backend/):  .venv\\Scripts\\python -m app.migrar
"""

import asyncio
import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.core import db
from app.core.config import obtener_settings

CARPETA = Path(__file__).resolve().parents[1] / "migraciones"


def cargar(ruta: Path):
    spec = importlib.util.spec_from_file_location(ruta.stem, ruta)
    modulo = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(modulo)  # type: ignore[union-attr]
    return modulo


async def main() -> int:
    base = await db.conectar(obtener_settings())
    try:
        aplicadas = {d["_id"] async for d in base["_migraciones"].find({}, {"_id": 1})}
        pendientes = [
            r for r in sorted(CARPETA.glob("[0-9][0-9][0-9][0-9]_*.py")) if r.stem not in aplicadas
        ]
        if not pendientes:
            print("Sin migraciones pendientes.")
        for ruta in pendientes:
            print(f"Aplicando {ruta.stem}...")
            await cargar(ruta).aplicar(base)
            await base["_migraciones"].insert_one(
                {"_id": ruta.stem, "aplicada_en": datetime.now(UTC)}
            )
        return 0
    finally:
        await db.desconectar()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
