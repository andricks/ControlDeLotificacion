"""Quita la copia de las condiciones generales guardada en `configuracion`.

El PDF las lee ahora directamente de `app/modules/configuracion/textos.py`; la copia en la
BD quedaba desactualizada al editar ese archivo.
"""

from app.modules.configuracion.textos import CONDICIONES_GENERALES


async def aplicar(db) -> None:
    await db["configuracion"].update_many(
        {"condiciones_generales": {"$exists": True}}, {"$unset": {"condiciones_generales": ""}}
    )


async def revertir(db) -> None:
    clausulas = [{"titulo": t, "texto": x} for t, x in CONDICIONES_GENERALES]
    await db["configuracion"].update_many(
        {"condiciones_generales": {"$exists": False}},
        {"$set": {"condiciones_generales": clausulas}},
    )
