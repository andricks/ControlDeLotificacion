"""Asigna la lotificación "tablon_campestre2" a las promesas, recibos y lotes anteriores a 0006.

Guarda los ids modificados en `_migracion_0007` para que `revertir` deshaga solo esos.
"""

LOTIFICACION = "tablon_campestre2"
COLECCIONES = ("contratos", "recibos", "lotes")
REGISTRO = "_migracion_0007"


async def aplicar(db) -> None:
    for nombre in COLECCIONES:
        filtro = {"lotificacion": None}
        ids = [d["_id"] async for d in db[nombre].find(filtro, {"_id": 1})]
        if not ids:
            continue
        await db[REGISTRO].update_one(
            {"_id": nombre}, {"$addToSet": {"ids": {"$each": ids}}}, upsert=True
        )
        await db[nombre].update_many(
            {"_id": {"$in": ids}}, {"$set": {"lotificacion": LOTIFICACION}}
        )


async def revertir(db) -> None:
    async for registro in db[REGISTRO].find({}):
        await db[registro["_id"]].update_many(
            {"_id": {"$in": registro["ids"]}}, {"$set": {"lotificacion": None}}
        )
    await db[REGISTRO].drop()
