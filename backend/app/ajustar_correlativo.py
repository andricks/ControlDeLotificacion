"""Continúa la numeración del papel: el siguiente número será (último usado + 1).

Uso (desde backend/):
    .venv\\Scripts\\python -m app.ajustar_correlativo recibo 2540
    .venv\\Scripts\\python -m app.ajustar_correlativo contrato 184

Nunca retrocede el contador (usa $max), así no se pueden repetir números ya emitidos.
"""

import asyncio
import sys

from pymongo.asynchronous.database import AsyncDatabase

from app.core import db
from app.core.config import obtener_settings

CONTADORES = {"recibo", "contrato"}


async def ajustar(base: AsyncDatabase, nombre: str, ultimo_usado: int) -> int:
    if nombre not in CONTADORES:
        raise ValueError(f"Contador desconocido: {nombre} (use {', '.join(sorted(CONTADORES))})")
    if ultimo_usado < 0:
        raise ValueError("El número debe ser positivo")
    await base["contadores"].update_one(
        {"_id": nombre}, {"$max": {"valor": ultimo_usado}}, upsert=True
    )
    doc = await base["contadores"].find_one({"_id": nombre})
    return int(doc["valor"])


async def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[1].isdigit():
        print(__doc__)
        return 1
    base = await db.conectar(obtener_settings())
    try:
        valor = await ajustar(base, argv[0], int(argv[1]))
        print(f"Contador '{argv[0]}' en {valor}: el siguiente número será {valor + 1}.")
        return 0
    finally:
        await db.desconectar()


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
