"""Reglas de negocio del Recibo de Caja.

Registrar y anular son transacciones: recibo + saldos del contrato + plan de cuotas +
estado del lote + auditoría se escriben juntos o no se escribe nada.
"""

import re
from datetime import date
from decimal import Decimal

from beanie import PydanticObjectId
from pymongo.asynchronous.client_session import AsyncClientSession

from app.core import db
from app.core.errores import Conflicto, NoEncontrado, ReglaNegocio
from app.core.formato import MESES
from app.core.letras import monto_a_letras
from app.core.tipos import CERO, ahora
from app.modules.auditoria.models import registrar
from app.modules.configuracion.models import Configuracion, obtener_configuracion
from app.modules.contratos import calculos
from app.modules.contratos import service as contratos_service
from app.modules.contratos.models import Contrato
from app.modules.contratos.schemas import CuotaPlan
from app.modules.contratos.service import reprogramar_pendientes
from app.modules.lotes.models import Lote
from app.modules.recibos.models import Recibo
from app.modules.recibos.schemas import ReciboCrear, ReciboLeer, SugerenciaPago


def mes_texto(fecha: date) -> str:
    """'octubre, 2025' — como en el recibo en papel."""
    return f"{MESES[fecha.month - 1].lower()}, {fecha.year}"


def primera_pendiente(plan: list[CuotaPlan]) -> CuotaPlan | None:
    return next((q for q in plan if q.estado != "pagada"), None)


async def _contrato(contrato_id: PydanticObjectId, session=None) -> Contrato:
    return await contratos_service.obtener(contrato_id, session=session)


async def sugerir(contrato_id: PydanticObjectId, fecha: date) -> SugerenciaPago:
    contrato = await _contrato(contrato_id)
    reglas = (await obtener_configuracion()).reglas
    cuota = primera_pendiente(contrato.plan_cuotas)
    gracia = reglas.dias_gracia
    vencidas = sum(
        1
        for q in contrato.plan_cuotas
        if q.estado != "pagada" and (fecha - q.vencimiento).days > gracia
    )
    capital = intereses = mora = CERO
    dias = 0
    if cuota:
        capital, intereses = cuota.capital_pendiente, cuota.interes_pendiente
        dias, mora = calculos.mora_sugerida(
            cuota.cuota, cuota.vencimiento, fecha, gracia, reglas.mora_pct_mensual
        )
    return SugerenciaPago(
        contrato_id=str(contrato.id),
        fecha=fecha,
        saldo_capital=contrato.saldo_capital,
        enganche_pendiente=contrato.condiciones.enganche - contrato.total_pagado_enganche,
        cuota_numero=cuota.numero if cuota else None,
        cuota_mes=mes_texto(cuota.vencimiento) if cuota else None,
        vencimiento=cuota.vencimiento if cuota else None,
        capital=capital,
        intereses=intereses,
        dias_atraso=dias,
        recargo_mora=mora,
        total_sugerido=capital + intereses + mora,
        cuotas_vencidas=vencidas,
    )


def _aplicar_cuota(plan: list[CuotaPlan], datos: ReciboCrear) -> CuotaPlan:
    pendiente = primera_pendiente(plan)
    if pendiente is None:
        raise ReglaNegocio("El contrato no tiene cuotas pendientes")
    if datos.cuota_numero != pendiente.numero:
        raise ReglaNegocio(
            f"Las cuotas se pagan en orden: la siguiente pendiente es la No. {pendiente.numero}",
            campos={"cuota_numero": "fuera_de_orden"},
        )
    d = datos.desglose
    if d.capital > pendiente.capital_pendiente:
        raise ReglaNegocio(
            f"El capital excede lo pendiente de la cuota ({pendiente.capital_pendiente:,.2f}); "
            "registre el excedente como abono a capital",
            campos={"desglose.capital": "excede_cuota"},
        )
    if d.intereses > pendiente.interes_pendiente:
        raise ReglaNegocio(
            f"Los intereses exceden lo pendiente de la cuota ({pendiente.interes_pendiente:,.2f})",
            campos={"desglose.intereses": "excede_cuota"},
        )
    pendiente.capital_pagado += d.capital
    pendiente.interes_pagado += d.intereses
    completa = pendiente.capital_pendiente == 0 and pendiente.interes_pendiente == 0
    pendiente.estado = "pagada" if completa else "parcial"
    return pendiente


def _validar_abono(
    plan: list[CuotaPlan], datos: ReciboCrear, saldo: Decimal, config: Configuracion
) -> None:
    abono = datos.desglose.abono_capital
    minimo = config.reglas.abono_capital_minimo
    if abono < minimo and abono != saldo:
        raise ReglaNegocio(
            f"El abono a capital no puede ser menor de Q {minimo:,.2f} (salvo para cancelar "
            "el saldo total)",
            campos={"desglose.abono_capital": "menor_al_minimo"},
        )
    atrasadas = [q.numero for q in plan if q.estado != "pagada" and q.vencimiento < datos.fecha]
    if atrasadas:
        raise ReglaNegocio(
            "Para abonar a capital el cliente debe estar al día; cuotas pendientes: "
            + ", ".join(map(str, atrasadas)),
            campos={"desglose.abono_capital": "cuotas_atrasadas"},
        )
    if any(q.estado == "parcial" for q in plan):
        raise ReglaNegocio(
            "Complete la cuota en curso antes de abonar a capital",
            campos={"desglose.abono_capital": "cuota_parcial"},
        )


async def registrar_recibo(datos: ReciboCrear, contrato_id: PydanticObjectId) -> Recibo:
    config = await obtener_configuracion()

    async def _transaccion(session: AsyncClientSession) -> Recibo:
        contrato = await _contrato(contrato_id, session=session)
        if contrato.estado != "vigente":
            raise ReglaNegocio(f"La promesa No. {contrato.numero_formateado} no está vigente")
        d = datos.desglose
        plan_anterior = [q.model_copy() for q in contrato.plan_cuotas]
        plan = [q.model_copy() for q in contrato.plan_cuotas]
        saldo_anterior = contrato.saldo_capital
        estado_anterior = contrato.estado
        cuota_mes = None

        if datos.concepto == "enganche":
            pendiente = contrato.condiciones.enganche - contrato.total_pagado_enganche
            if d.enganche > pendiente:
                raise ReglaNegocio(
                    f"El enganche pendiente es Q {pendiente:,.2f}",
                    campos={"desglose.enganche": "excede_pendiente"},
                )
            contrato.total_pagado_enganche += d.enganche

        if datos.concepto == "cuota":
            cuota = _aplicar_cuota(plan, datos)
            cuota_mes = mes_texto(cuota.vencimiento)

        if d.reduce_saldo > saldo_anterior:
            raise ReglaNegocio(
                f"El pago a capital excede el saldo actual (Q {saldo_anterior:,.2f})",
                campos={"desglose.abono_capital": "excede_saldo"},
            )
        saldo_actual = saldo_anterior - d.reduce_saldo

        if d.abono_capital > 0:
            _validar_abono(plan, datos, saldo_anterior - d.capital, config)
            plan = reprogramar_pendientes(plan, saldo_actual, contrato.condiciones)

        numero = await db.siguiente_correlativo("recibo", session=session)
        recibo = Recibo(
            numero=numero,
            numero_fel=datos.numero_fel,
            lugar=config.ciudad_documentos,
            fecha=datos.fecha,
            contrato_id=contrato.id,
            contrato_numero=contrato.numero,
            cliente_id=contrato.cliente_id,
            cliente_nombre=contrato.comprador.nombres_apellidos,
            lotificacion=contrato.lotificacion,
            lotes_texto=contrato.lote.codigo,
            concepto=datos.concepto,
            cuota_numero=datos.cuota_numero,
            cuota_mes=cuota_mes,
            desglose=d,
            total=d.total,
            total_en_letras=monto_a_letras(d.total),
            saldo_anterior=saldo_anterior,
            saldo_actual=saldo_actual,
            boletas=datos.boletas,
            observaciones=datos.observaciones,
            plan_anterior=plan_anterior,
            estado_contrato_anterior=estado_anterior,
        )
        await recibo.insert(session=session)

        contrato.plan_cuotas = plan
        contrato.saldo_capital = saldo_actual
        contrato.total_pagado_capital += d.reduce_saldo
        contrato.actualizado_en = ahora()
        if saldo_actual == 0 and contrato.total_pagado_enganche >= contrato.condiciones.enganche:
            contrato.estado = "cancelado_total"
            await _actualizar_lote(contrato, "vendido", session)
        await contrato.save(session=session)
        await registrar(
            "crear",
            "recibos",
            recibo.id,
            {"numero": numero, "contrato": contrato.numero, "total": str(d.total)},
            session=session,
        )
        return recibo

    async with db.obtener_cliente().start_session() as session:
        return await session.with_transaction(_transaccion)


async def _actualizar_lote(contrato: Contrato, estado: str, session) -> None:
    lote = await Lote.get(contrato.lote_id, session=session)
    if lote:
        lote.estado = estado
        lote.actualizado_en = ahora()
        await lote.save(session=session)


async def _revertir(recibo: Recibo, accion: str, session: AsyncClientSession) -> None:
    """Deja el contrato como estaba antes del recibo. Solo vale para el último recibo vigente
    del contrato (así los saldos quedan exactos)."""
    ultimo = (
        await Recibo.find(
            Recibo.contrato_id == recibo.contrato_id,
            Recibo.anulado == False,  # noqa: E712
            Recibo.eliminado_en == None,  # noqa: E711
            session=session,
        )
        .sort("-numero")
        .limit(1)
        .to_list()
    )
    if ultimo and ultimo[0].id != recibo.id:
        raise Conflicto(
            f"Solo puede {accion} el último recibo del contrato "
            f"(No. {ultimo[0].numero_formateado})",
            codigo="NO_ES_ULTIMO_RECIBO",
        )
    contrato = await _contrato(recibo.contrato_id, session=session)
    d = recibo.desglose
    contrato.plan_cuotas = recibo.plan_anterior
    contrato.saldo_capital = recibo.saldo_anterior
    contrato.total_pagado_capital -= d.reduce_saldo
    contrato.total_pagado_enganche -= d.enganche
    if contrato.estado != recibo.estado_contrato_anterior:
        contrato.estado = recibo.estado_contrato_anterior
        await _actualizar_lote(contrato, "reservado", session)
    contrato.actualizado_en = ahora()
    await contrato.save(session=session)


async def anular(recibo_id: PydanticObjectId, motivo: str) -> Recibo:
    """Solo se anula el último recibo vigente del contrato (así los saldos quedan exactos)."""

    async def _transaccion(session: AsyncClientSession) -> Recibo:
        recibo = await obtener(recibo_id, session=session)
        if recibo.anulado:
            raise Conflicto("El recibo ya está anulado")
        await _revertir(recibo, "anularse", session)
        recibo.anulado, recibo.motivo_anulacion, recibo.anulado_en = True, motivo, ahora()
        await recibo.save(session=session)
        await registrar(
            "anular",
            "recibos",
            recibo.id,
            {"numero": recibo.numero, "motivo": motivo},
            session=session,
        )
        return recibo

    async with db.obtener_cliente().start_session() as session:
        return await session.with_transaction(_transaccion)


async def eliminar(recibo_id: PydanticObjectId, motivo: str) -> Recibo:
    """Borrado lógico. Un recibo vigente primero revierte su efecto en el contrato (solo el
    último); uno ya anulado no afecta saldos y se puede borrar siempre."""

    async def _transaccion(session: AsyncClientSession) -> Recibo:
        recibo = await obtener(recibo_id, session=session)
        if not recibo.anulado:
            await _revertir(recibo, "borrarse", session)
        recibo.eliminado_en, recibo.motivo_eliminacion = ahora(), motivo
        await recibo.save(session=session)
        await registrar(
            "eliminar",
            "recibos",
            recibo.id,
            {"numero": recibo.numero, "motivo": motivo, "estaba_anulado": recibo.anulado},
            session=session,
        )
        return recibo

    async with db.obtener_cliente().start_session() as session:
        return await session.with_transaction(_transaccion)


async def obtener(recibo_id: PydanticObjectId, session=None) -> Recibo:
    recibo = await Recibo.get(recibo_id, session=session)
    if recibo is None or recibo.eliminado_en is not None:
        raise NoEncontrado("Recibo no encontrado")
    return recibo


async def buscar(
    texto: str | None, contrato_id: PydanticObjectId | None, pagina: int, tamano: int
) -> tuple[list[Recibo], int]:
    condiciones: list[dict] = [{"eliminado_en": None}]
    if contrato_id:
        condiciones.append({"contrato_id": contrato_id})
    if texto and texto.strip():
        t = texto.strip()
        opciones: list[dict] = [
            {"cliente_nombre": {"$regex": re.escape(t), "$options": "i"}},
            {"lotes_texto": {"$regex": re.escape(t), "$options": "i"}},
            {"numero_fel": {"$regex": re.escape(t), "$options": "i"}},
        ]
        if t.isdigit():
            opciones.append({"numero": int(t)})
        condiciones.append({"$or": opciones})
    consulta = Recibo.find({"$and": condiciones})
    total = await consulta.count()
    items = await consulta.sort("-numero").skip((pagina - 1) * tamano).limit(tamano).to_list()
    return items, total


async def de_contrato(contrato_id: PydanticObjectId) -> list[Recibo]:
    return (
        await Recibo.find(
            Recibo.contrato_id == contrato_id,
            Recibo.eliminado_en == None,  # noqa: E711
        )
        .sort("+numero")
        .to_list()
    )


def a_leer(r: Recibo) -> ReciboLeer:
    datos = r.model_dump(
        exclude={
            "id",
            "revision_id",
            "contrato_id",
            "cliente_id",
            "plan_anterior",
            "estado_contrato_anterior",
            "eliminado_en",
            "motivo_eliminacion",
        }
    )
    return ReciboLeer(
        **datos,
        id=str(r.id),
        numero_formateado=r.numero_formateado,
        contrato_id=str(r.contrato_id),
        cliente_id=str(r.cliente_id),
    )
