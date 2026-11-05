from beanie import PydanticObjectId
from bson.errors import InvalidId

from app.core.errores import NoEncontrado


def parsear_id(valor: str, recurso: str = "Recurso") -> PydanticObjectId:
    """Convierte el id de la URL; un id mal formado se trata como 'no encontrado'."""
    try:
        return PydanticObjectId(valor)
    except (InvalidId, TypeError) as e:
        raise NoEncontrado(f"{recurso} no encontrado") from e
