from datetime import datetime
from typing import Literal

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel
from pymongo.asynchronous.client_session import AsyncClientSession

from app.core.errores import Conflicto
from app.core.tipos import ahora
from app.modules.lotes.schemas import LOTIFICACIONES, LoteDatos, Lotificacion

EstadoLote = Literal["disponible", "reservado", "vendido"]


class Lote(Document, LoteDatos):
    # None = lote registrado antes de poder elegir lotificación (migración 0006).
    lotificacion: Lotificacion | None = None
    estado: EstadoLote = "disponible"
    contrato_id: PydanticObjectId | None = None
    creado_en: datetime = Field(default_factory=ahora)
    actualizado_en: datetime | None = None

    class Settings:
        name = "lotes"
        indexes = [
            # el mismo número de lote puede existir en distintas lotificaciones
            IndexModel([("lotificacion", ASCENDING), ("codigo", ASCENDING)], unique=True),
            IndexModel([("estado", ASCENDING)]),
        ]


async def reservar(
    datos: LoteDatos, lotificacion: Lotificacion, session: AsyncClientSession | None = None
) -> Lote:
    """Obtiene o crea el lote y lo marca como reservado; falla si ya está comprometido."""
    lote = await Lote.find_one(
        Lote.lotificacion == lotificacion, Lote.codigo == datos.codigo, session=session
    )
    if lote is None:
        lote = Lote(**datos.model_dump(), lotificacion=lotificacion)
    elif lote.estado != "disponible":
        raise Conflicto(
            f"El lote {datos.codigo} de {LOTIFICACIONES[lotificacion]} ya está asignado a otra "
            "promesa de compra-venta",
            codigo="LOTE_NO_DISPONIBLE",
            campos={"lote.codigo": "no_disponible"},
        )
    else:
        for campo, valor in datos.model_dump().items():
            setattr(lote, campo, valor)
        lote.actualizado_en = ahora()
    lote.estado = "reservado"
    await lote.save(session=session)
    return lote
