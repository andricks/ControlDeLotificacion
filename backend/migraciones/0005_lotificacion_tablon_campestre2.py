"""Renombra el proyecto a Lotificación "Tablon Campestre2"."""

PROYECTO_NUEVO = 'LOTIFICACIÓN "TABLON CAMPESTRE2"'
PROYECTO_ANTERIOR = 'LOTIFICACIÓN "MONACO"'


async def aplicar(db) -> None:
    await db["configuracion"].update_many({}, {"$set": {"proyecto": PROYECTO_NUEVO}})


async def revertir(db) -> None:
    await db["configuracion"].update_many({}, {"$set": {"proyecto": PROYECTO_ANTERIOR}})
