import re

from beanie import PydanticObjectId
from pymongo.asynchronous.client_session import AsyncClientSession

from app.core.errores import NoEncontrado
from app.core.tipos import ahora
from app.core.validaciones import normalizar_dpi
from app.modules.clientes.models import Cliente
from app.modules.clientes.schemas import ClienteDatos, ClienteLeer


def a_leer(cliente: Cliente) -> ClienteLeer:
    return ClienteLeer(
        id=str(cliente.id), **cliente.model_dump(include=set(ClienteDatos.model_fields))
    )


async def guardar_por_dpi(
    datos: ClienteDatos, session: AsyncClientSession | None = None
) -> Cliente:
    """Crea el cliente o actualiza sus datos si ya existe uno con el mismo DPI."""
    existente = await Cliente.find_one(Cliente.dpi == datos.dpi, session=session)
    if existente is None:
        return await Cliente(**datos.model_dump()).insert(session=session)
    for campo, valor in datos.model_dump().items():
        setattr(existente, campo, valor)
    existente.actualizado_en = ahora()
    await existente.save(session=session)
    return existente


async def obtener(cliente_id: PydanticObjectId) -> Cliente:
    cliente = await Cliente.get(cliente_id)
    if cliente is None:
        raise NoEncontrado("Cliente no encontrado")
    return cliente


async def obtener_por_dpi(dpi: str) -> Cliente:
    cliente = await Cliente.find_one(Cliente.dpi == normalizar_dpi(dpi))
    if cliente is None:
        raise NoEncontrado("No hay un cliente registrado con ese DPI")
    return cliente


async def buscar(texto: str | None, pagina: int, tamano: int) -> tuple[list[Cliente], int]:
    filtro: dict = {}
    if texto:
        patron = re.escape(texto.strip())
        filtro = {
            "$or": [
                {"nombres_apellidos": {"$regex": patron, "$options": "i"}},
                {"dpi": {"$regex": f"^{re.escape(normalizar_dpi(texto))}"}},
            ]
        }
    consulta = Cliente.find(filtro)
    total = await consulta.count()
    items = (
        await consulta.sort("+nombres_apellidos")
        .skip((pagina - 1) * tamano)
        .limit(tamano)
        .to_list()
    )
    return items, total
