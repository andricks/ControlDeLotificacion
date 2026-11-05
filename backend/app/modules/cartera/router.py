import asyncio
from datetime import date

from fastapi import APIRouter, Query, Response

from app.core.tipos import hoy_guatemala
from app.modules.auditoria.models import registrar
from app.modules.cartera import service
from app.modules.cartera.schemas import CarteraLeer, SituacionPago
from app.modules.configuracion.models import ConfiguracionDatos, obtener_configuracion
from app.modules.lotes.schemas import Lotificacion
from app.pdf.cartera import construir_reporte_cartera

router = APIRouter(prefix="/cartera", tags=["cartera"])


@router.get(
    "",
    response_model=CarteraLeer,
    summary="Cartera de cobro: morosos, próximos pagos y día de pago de cada cliente",
)
async def listar(
    situacion: SituacionPago | None = None,
    buscar: str | None = Query(default=None, max_length=100),
    lotificacion: Lotificacion | None = None,
    fecha: date | None = None,  # fecha de corte; por defecto, hoy en Guatemala
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
) -> CarteraLeer:
    return await service.cartera(
        fecha or hoy_guatemala(), situacion, buscar, lotificacion, pagina, tamano
    )


@router.get(
    "/pdf",
    summary="Descargar Reporte de Cobros (morosos u otra situación) en PDF",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def descargar_pdf(
    situacion: SituacionPago | None = None,
    buscar: str | None = Query(default=None, max_length=100),
    lotificacion: Lotificacion | None = None,
    fecha: date | None = None,
    en_linea: bool = False,
) -> Response:
    corte = fecha or hoy_guatemala()
    cartera = await service.cartera(corte, situacion, buscar, lotificacion)
    config = ConfiguracionDatos(**(await obtener_configuracion()).model_dump())
    contenido = await asyncio.to_thread(
        construir_reporte_cartera, cartera, situacion, lotificacion, config
    )
    detalle = {"situacion": situacion, "lotificacion": lotificacion, "clientes": cartera.total}
    await registrar("descargar_reporte_cobros", "contratos", None, detalle)
    nombre = f"cobros_{situacion or 'todos'}_{corte.isoformat()}.pdf"
    disposicion = "inline" if en_linea else "attachment"
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposicion}; filename="{nombre}"',
            "Cache-Control": "no-store",
        },
    )
