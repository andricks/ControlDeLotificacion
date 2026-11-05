import asyncio
import re
from datetime import UTC, date, datetime

from fastapi import APIRouter, Query, Response, status

from app.core.ids import parsear_id
from app.core.tipos import Pagina
from app.modules.auditoria.models import registrar
from app.modules.configuracion.models import ConfiguracionDatos, obtener_configuracion
from app.modules.contratos import service as contratos_service
from app.modules.contratos.schemas import Eliminar
from app.modules.recibos import service
from app.modules.recibos.schemas import ReciboAnular, ReciboCrear, ReciboLeer, SugerenciaPago
from app.pdf.estado_cuenta import construir_estado_cuenta
from app.pdf.recibo import construir_recibo

router = APIRouter(tags=["recibos"])


def _pdf(contenido: bytes, nombre: str, en_linea: bool) -> Response:
    disposicion = "inline" if en_linea else "attachment"
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposicion}; filename="{nombre}"',
            "Cache-Control": "no-store",
        },
    )


async def _config() -> ConfiguracionDatos:
    return ConfiguracionDatos(**(await obtener_configuracion()).model_dump())


@router.get(
    "/recibos/sugerencia",
    response_model=SugerenciaPago,
    summary="Siguiente pago sugerido: cuota, mes, capital, intereses y mora",
)
async def sugerencia(contrato_id: str, fecha: date | None = None) -> SugerenciaPago:
    return await service.sugerir(parsear_id(contrato_id, "Promesa"), fecha or date.today())


@router.post(
    "/recibos",
    response_model=ReciboLeer,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar Recibo de Caja (actualiza saldo y plan de cuotas)",
)
async def crear(datos: ReciboCrear) -> ReciboLeer:
    contrato_id = parsear_id(datos.contrato_id, "Promesa")
    return service.a_leer(await service.registrar_recibo(datos, contrato_id))


@router.get("/recibos", response_model=Pagina[ReciboLeer], summary="Listar y buscar recibos")
async def listar(
    buscar: str | None = Query(default=None, max_length=100),
    contrato_id: str | None = None,
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
) -> Pagina[ReciboLeer]:
    cid = parsear_id(contrato_id, "Promesa") if contrato_id else None
    items, total = await service.buscar(buscar, cid, pagina, tamano)
    return Pagina(
        items=[service.a_leer(r) for r in items], total=total, pagina=pagina, tamano=tamano
    )


@router.get("/recibos/{recibo_id}", response_model=ReciboLeer, summary="Obtener recibo")
async def obtener(recibo_id: str) -> ReciboLeer:
    return service.a_leer(await service.obtener(parsear_id(recibo_id, "Recibo")))


@router.post(
    "/recibos/{recibo_id}/anular",
    response_model=ReciboLeer,
    summary="Anular el último recibo de un contrato (revierte saldo y plan)",
)
async def anular(recibo_id: str, datos: ReciboAnular) -> ReciboLeer:
    return service.a_leer(await service.anular(parsear_id(recibo_id, "Recibo"), datos.motivo))


@router.post(
    "/recibos/{recibo_id}/eliminar",
    response_model=ReciboLeer,
    summary="Borrar un recibo (si está vigente debe ser el último; revierte saldo y plan)",
)
async def eliminar(recibo_id: str, datos: Eliminar) -> ReciboLeer:
    return service.a_leer(await service.eliminar(parsear_id(recibo_id, "Recibo"), datos.motivo))


@router.get(
    "/recibos/{recibo_id}/pdf",
    summary="Descargar Recibo de Caja en PDF (original y copia)",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def descargar_pdf(recibo_id: str, en_linea: bool = False) -> Response:
    recibo = await service.obtener(parsear_id(recibo_id, "Recibo"))
    leer = service.a_leer(recibo)
    contenido = await asyncio.to_thread(construir_recibo, leer, await _config())
    await registrar("descargar_pdf", "recibos", recibo.id, {"numero": recibo.numero})
    lote = re.sub(r"[^A-Za-z0-9-]", "", recibo.lotes_texto)
    return _pdf(contenido, f"recibo_{leer.numero_formateado}_lote_{lote}.pdf", en_linea)


@router.get(
    "/contratos/{contrato_id}/estado-cuenta/pdf",
    summary="Descargar Estado de Cuenta de la promesa en PDF",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def estado_cuenta_pdf(contrato_id: str, en_linea: bool = False) -> Response:
    cid = parsear_id(contrato_id, "Promesa")
    contrato = contratos_service.a_leer(await contratos_service.obtener(cid))
    recibos = [service.a_leer(r) for r in await service.de_contrato(cid)]
    contenido = await asyncio.to_thread(
        construir_estado_cuenta, contrato, recibos, await _config(), datetime.now(UTC)
    )
    await registrar("descargar_estado_cuenta", "contratos", cid, {"numero": contrato.numero})
    return _pdf(contenido, f"estado_cuenta_{contrato.numero_formateado}.pdf", en_linea)
