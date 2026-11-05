from fastapi import APIRouter, Query

from app.core.ids import parsear_id
from app.core.tipos import Pagina
from app.modules.clientes import service
from app.modules.clientes.schemas import ClienteLeer

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("", response_model=Pagina[ClienteLeer], summary="Buscar clientes por nombre o DPI")
async def listar(
    buscar: str | None = Query(default=None, max_length=100),
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
) -> Pagina[ClienteLeer]:
    items, total = await service.buscar(buscar, pagina, tamano)
    return Pagina(
        items=[service.a_leer(c) for c in items], total=total, pagina=pagina, tamano=tamano
    )


@router.get(
    "/por-dpi/{dpi}",
    response_model=ClienteLeer,
    summary="Obtener cliente por DPI (para autocompletar el formulario)",
)
async def por_dpi(dpi: str) -> ClienteLeer:
    return service.a_leer(await service.obtener_por_dpi(dpi))


@router.get("/{cliente_id}", response_model=ClienteLeer, summary="Obtener cliente")
async def obtener(cliente_id: str) -> ClienteLeer:
    return service.a_leer(await service.obtener(parsear_id(cliente_id, "Cliente")))
