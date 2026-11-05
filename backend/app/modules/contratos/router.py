import asyncio
import re

from fastapi import APIRouter, Query, Response, status

from app.core.ids import parsear_id
from app.core.tipos import Pagina
from app.modules.auditoria.models import registrar
from app.modules.configuracion.models import ConfiguracionDatos, obtener_configuracion
from app.modules.contratos import service
from app.modules.contratos.schemas import (
    CalculoEntrada,
    CalculoLeer,
    ContratoCrear,
    ContratoLeer,
    ContratoResumen,
    EliminadoLeer,
    Eliminar,
    EstadoContrato,
)
from app.pdf.promesa import construir_promesa

router = APIRouter(prefix="/contratos", tags=["contratos"])


@router.post(
    "/calcular",
    response_model=CalculoLeer,
    summary="Vista previa: calcula totales y plan de cuotas sin guardar",
)
async def calcular(entrada: CalculoEntrada) -> CalculoLeer:
    return service.calcular(entrada.condiciones)


@router.post(
    "",
    response_model=ContratoLeer,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Promesa de Compra Venta (guarda cliente, reserva lote y numera)",
)
async def crear(datos: ContratoCrear) -> ContratoLeer:
    return service.a_leer(await service.crear(datos))


@router.get("", response_model=Pagina[ContratoResumen], summary="Listar y buscar promesas")
async def listar(
    buscar: str | None = Query(default=None, max_length=100),
    estado: EstadoContrato | None = None,
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
) -> Pagina[ContratoResumen]:
    items, total = await service.buscar(buscar, estado, pagina, tamano)
    return Pagina(
        items=[service.a_resumen(c) for c in items], total=total, pagina=pagina, tamano=tamano
    )


@router.get("/{contrato_id}", response_model=ContratoLeer, summary="Obtener promesa")
async def obtener(contrato_id: str) -> ContratoLeer:
    return service.a_leer(await service.obtener(parsear_id(contrato_id, "Promesa")))


@router.post(
    "/{contrato_id}/eliminar",
    response_model=EliminadoLeer,
    summary="Borrar promesa (también sus recibos; el lote queda disponible)",
)
async def eliminar(contrato_id: str, datos: Eliminar) -> EliminadoLeer:
    return await service.eliminar(parsear_id(contrato_id, "Promesa"), datos.motivo)


@router.get(
    "/{contrato_id}/pdf",
    summary="Descargar Promesa de Compra Venta en PDF",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def descargar_pdf(contrato_id: str, en_linea: bool = False) -> Response:
    contrato = service.a_leer(await service.obtener(parsear_id(contrato_id, "Promesa")))
    config = ConfiguracionDatos(**(await obtener_configuracion()).model_dump())
    contenido = await asyncio.to_thread(construir_promesa, contrato, config)
    await registrar(
        "descargar_pdf", "contratos", parsear_id(contrato.id), {"numero": contrato.numero}
    )
    lote = re.sub(r"[^A-Za-z0-9-]", "", contrato.lote.codigo)
    nombre = f"promesa_{contrato.numero_formateado}_lote_{lote}.pdf"
    disposicion = "inline" if en_linea else "attachment"
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposicion}; filename="{nombre}"',
            "Cache-Control": "no-store",
        },
    )
