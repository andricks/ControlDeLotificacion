from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.asynchronous.client_session import AsyncClientSession

from app.core.seguridad import usuario_en_curso
from app.core.tipos import ahora


class Auditoria(Document):
    usuario: str = "sistema"  # correo del usuario autenticado; "sistema" en scripts
    accion: str
    coleccion: str
    documento_id: PydanticObjectId | None = None
    detalle: dict[str, Any] = Field(default_factory=dict)
    fecha: datetime = Field(default_factory=ahora)

    class Settings:
        name = "auditoria"
        indexes = [
            IndexModel([("fecha", DESCENDING)]),
            IndexModel([("coleccion", ASCENDING), ("documento_id", ASCENDING)]),
            # Intentos de acceso de cuentas no autorizadas: se borran solos a los 90 días.
            IndexModel(
                [("fecha", ASCENDING)],
                name="ttl_rechazos",
                expireAfterSeconds=90 * 24 * 3600,
                partialFilterExpression={"accion": "inicio_sesion_rechazado"},
            ),
        ]


async def registrar(
    accion: str,
    coleccion: str,
    documento_id: PydanticObjectId | None = None,
    detalle: dict[str, Any] | None = None,
    session: AsyncClientSession | None = None,
    usuario: str | None = None,
) -> None:
    """Registra una acción. No guardar aquí datos personales (DPI, direcciones).

    El usuario es, por defecto, el de la sesión de la petición en curso.
    """
    await Auditoria(
        usuario=usuario or usuario_en_curso.get(),
        accion=accion,
        coleccion=coleccion,
        documento_id=documento_id,
        detalle=detalle or {},
    ).insert(session=session)
