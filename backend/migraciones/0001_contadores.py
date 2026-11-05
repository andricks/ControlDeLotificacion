"""Crea los contadores de correlativos (contrato y recibo) si no existen.

Para continuar la numeración del papel, ajustar el valor inicial con un script posterior
(valor = último número usado).
"""


async def aplicar(db) -> None:
    for nombre in ("contrato", "recibo"):
        await db["contadores"].update_one(
            {"_id": nombre}, {"$setOnInsert": {"valor": 0}}, upsert=True
        )


async def revertir(db) -> None:
    await db["contadores"].delete_many({"_id": {"$in": ["contrato", "recibo"]}, "valor": 0})
