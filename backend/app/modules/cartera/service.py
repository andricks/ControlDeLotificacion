"""Cartera de cobro: quién está moroso, a quién le toca pagar y cuándo.

Solo lectura: se calcula al vuelo desde el plan de cuotas de cada promesa vigente.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from beanie import PydanticObjectId

from app.core.tipos import CERO
from app.modules.cartera.schemas import (
    CarteraLeer,
    ClienteCartera,
    ResumenCartera,
    SituacionPago,
)
from app.modules.configuracion.models import ReglasNegocio, obtener_configuracion
from app.modules.contratos.calculos import mora_sugerida
from app.modules.contratos.models import Contrato
from app.modules.contratos.schemas import CuotaPlan
from app.modules.recibos.models import Recibo

DIAS_AVISO = 7  # "por vencer": la próxima cuota vence dentro de esta semana


@dataclass(frozen=True)
class Situacion:
    proxima: CuotaPlan | None
    cuotas_vencidas: int
    dias_atraso: int
    monto_vencido: Decimal
    mora_estimada: Decimal
    situacion: SituacionPago


def evaluar(plan: list[CuotaPlan], hoy: date, reglas: ReglasNegocio) -> Situacion:
    """Situación de pago al día `hoy`. Función pura (sin BD)."""
    pendientes = [q for q in plan if q.estado != "pagada"]
    vencidas = [q for q in pendientes if (hoy - q.vencimiento).days > reglas.dias_gracia]
    proxima = pendientes[0] if pendientes else None
    dias = max((hoy - proxima.vencimiento).days, 0) if proxima else 0
    monto = sum((q.capital_pendiente + q.interes_pendiente for q in vencidas), CERO)
    mora = sum(
        (
            mora_sugerida(q.cuota, q.vencimiento, hoy, reglas.dias_gracia, reglas.mora_pct_mensual)[
                1
            ]
            for q in vencidas
        ),
        CERO,
    )
    if vencidas:
        situacion: SituacionPago = "moroso"
    elif dias > 0:
        situacion = "en_gracia"
    elif proxima and (proxima.vencimiento - hoy).days <= DIAS_AVISO:
        situacion = "por_vencer"
    else:
        situacion = "al_dia"
    return Situacion(proxima, len(vencidas), dias, monto, mora, situacion)


def a_cliente(c: Contrato, s: Situacion, ultimo_pago: date | None) -> ClienteCartera:
    p = s.proxima
    return ClienteCartera(
        contrato_id=str(c.id),
        numero_formateado=c.numero_formateado,
        cliente_nombre=c.comprador.nombres_apellidos,
        telefono=c.comprador.telefono,
        lotificacion=c.lotificacion,
        lote_codigo=c.lote.codigo,
        dia_pago_mensual=c.condiciones.dia_pago_mensual,
        cuota_nivelada=c.condiciones.cuota_nivelada,
        numero_cuotas=len(c.plan_cuotas),
        cuotas_pagadas=sum(1 for q in c.plan_cuotas if q.estado == "pagada"),
        proxima_cuota_numero=p.numero if p else None,
        proxima_vencimiento=p.vencimiento if p else None,
        proxima_monto=p.capital_pendiente + p.interes_pendiente if p else CERO,
        cuotas_vencidas=s.cuotas_vencidas,
        dias_atraso=s.dias_atraso,
        monto_vencido=s.monto_vencido,
        mora_estimada=s.mora_estimada,
        enganche_pendiente=c.condiciones.enganche - c.total_pagado_enganche,
        saldo_capital=c.saldo_capital,
        ultimo_pago=ultimo_pago,
        situacion=s.situacion,
        riesgo_rescision=s.cuotas_vencidas >= 2,
    )


async def _ultimos_pagos(ids: list[PydanticObjectId]) -> dict[PydanticObjectId, date]:
    filas = await Recibo.aggregate(
        [
            {"$match": {"contrato_id": {"$in": ids}, "eliminado_en": None, "anulado": False}},
            {"$group": {"_id": "$contrato_id", "fecha": {"$max": "$fecha"}}},
        ]
    ).to_list()
    return {
        f["_id"]: f["fecha"].date() if isinstance(f["fecha"], datetime) else f["fecha"]
        for f in filas
    }


def _orden(c: ClienteCartera) -> tuple:
    # primero los más atrasados; luego por fecha de la próxima cuota (sin cuota al final)
    return (-c.dias_atraso, c.proxima_vencimiento or date.max, c.numero_formateado)


async def cartera(
    hoy: date,
    situacion: SituacionPago | None,
    texto: str | None,
    lotificacion: str | None,
    pagina: int = 1,
    tamano: int | None = None,
) -> CarteraLeer:
    """Cartera filtrada; `tamano=None` devuelve todos los clientes (reporte PDF)."""
    reglas = (await obtener_configuracion()).reglas
    condiciones: list[dict] = [{"eliminado_en": None}, {"estado": "vigente"}]
    if lotificacion:
        condiciones.append({"lotificacion": lotificacion})
    if texto and texto.strip():
        patron = re.escape(texto.strip())
        condiciones.append(
            {
                "$or": [
                    {"comprador.nombres_apellidos": {"$regex": patron, "$options": "i"}},
                    {"lote.codigo": {"$regex": patron, "$options": "i"}},
                ]
            }
        )
    contratos = await Contrato.find({"$and": condiciones}).to_list()
    pagos = await _ultimos_pagos([c.id for c in contratos])
    todos = sorted(
        (a_cliente(c, evaluar(c.plan_cuotas, hoy, reglas), pagos.get(c.id)) for c in contratos),
        key=_orden,
    )

    def contar(s: SituacionPago) -> int:
        return sum(1 for c in todos if c.situacion == s)

    resumen = ResumenCartera(
        clientes=len(todos),
        morosos=contar("moroso"),
        en_gracia=contar("en_gracia"),
        por_vencer=contar("por_vencer"),
        al_dia=contar("al_dia"),
        riesgo_rescision=sum(1 for c in todos if c.riesgo_rescision),
        monto_vencido=sum((c.monto_vencido for c in todos), CERO),
        mora_estimada=sum((c.mora_estimada for c in todos), CERO),
    )
    filtrados = [c for c in todos if situacion is None or c.situacion == situacion]
    tamano = tamano or max(len(filtrados), 1)
    inicio = (pagina - 1) * tamano
    return CarteraLeer(
        fecha=hoy,
        dias_gracia=reglas.dias_gracia,
        resumen=resumen,
        items=filtrados[inicio : inicio + tamano],
        total=len(filtrados),
        pagina=pagina,
        tamano=tamano,
    )
