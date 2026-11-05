"""Renombra el proyecto a Lotificación "Monaco" y agrega las cuentas bancarias de depósito.

La configuración ya existe en la BD, así que los nuevos valores por defecto del modelo no
le llegan solos.
"""

from app.modules.configuracion.models import ConfiguracionDatos

PROYECTO_ANTERIOR = 'RESIDENCIALES "BUENAVENTURA JALAPA III"'


async def aplicar(db) -> None:
    nuevos = ConfiguracionDatos()
    await db["configuracion"].update_many(
        {},
        {
            "$set": {
                "proyecto": nuevos.proyecto,
                "cuentas_bancarias": [c.model_dump() for c in nuevos.cuentas_bancarias],
            }
        },
    )


async def revertir(db) -> None:
    await db["configuracion"].update_many(
        {},
        {"$set": {"proyecto": PROYECTO_ANTERIOR}, "$unset": {"cuentas_bancarias": ""}},
    )
