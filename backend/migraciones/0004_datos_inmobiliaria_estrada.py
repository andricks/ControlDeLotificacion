"""Cambia los datos del emisor a Inmobiliaria Estrada (empresa, oficinas, teléfono, proyecto)."""

from app.modules.configuracion.models import ConfiguracionDatos

CAMPOS = ("empresa", "direccion_oficinas", "telefono_oficinas", "direccion_proyecto")

ANTERIORES = {
    "empresa": "INVERSIONES VELER, S.A.",
    "direccion_oficinas": '7a. Av. y 2da. Calle Zona 1, "Barrio La Democracia", Jalapa',
    "telefono_oficinas": "7937-9100",
    "direccion_proyecto": (
        "Aldea Las Margaritas Km. 99.5 RN-18, Carretera hacia San Pedro Pinula, Jalapa"
    ),
}


async def aplicar(db) -> None:
    nuevos = ConfiguracionDatos()
    await db["configuracion"].update_many(
        {}, {"$set": {campo: getattr(nuevos, campo) for campo in CAMPOS}}
    )


async def revertir(db) -> None:
    await db["configuracion"].update_many({}, {"$set": ANTERIORES})
