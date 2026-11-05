"""Reglas de negocio de la Promesa de Compra Venta."""

import re
from decimal import Decimal

from beanie import PydanticObjectId
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.errors import DuplicateKeyError

from app.core import db
from app.core.errores import Conflicto, NoEncontrado, ReglaNegocio
from app.core.tipos import CERO, ahora
from app.modules.auditoria.models import registrar
from app.modules.clientes import service as clientes_service
from app.modules.contratos import calculos
from app.modules.contratos.models import Contrato
from app.modules.contratos.schemas import (
    CalculoLeer,
    CondicionesContrato,
    CondicionesEntrada,
    ContratoCrear,
    ContratoLeer,
    ContratoResumen,
    CuotaPlan,
    EliminadoLeer,
    SaldoInicial,
)
from app.modules.lotes.models import Lote, reservar
from app.modules.recibos.models import Recibo


def calcular(entrada: CondicionesEntrada) -> CalculoLeer:
    """Totales + plan de cuotas. Función pura: sirve para la vista previa y para crear."""
    totales = calculos.calcular_totales(
        entrada.precio_terreno, entrada.mejoras, entrada.enganche, entrada.otros_descuentos
    )
    numero_cuotas = entrada.numero_cuotas or entrada.plazo_anios * 12
    dia_pago = entrada.dia_pago_mensual or entrada.fecha_primera_cuota.day
    plan = calculos.generar_plan(
        totales.saldo_a_pagar,
        numero_cuotas,
        entrada.tasa_interes_anual_pct,
        entrada.fecha_primera_cuota,
        dia_pago,
        cuota=entrada.cuota_nivelada,
    )
    cuota = plan[0].cuota if plan else CERO
    condiciones = CondicionesContrato(
        **entrada.model_dump(exclude={"numero_cuotas", "cuota_nivelada", "dia_pago_mensual"}),
        total=totales.total,
        saldo_a_pagar=totales.saldo_a_pagar,
        numero_cuotas=numero_cuotas,
        cuota_nivelada=entrada.cuota_nivelada or cuota,
        dia_pago_mensual=dia_pago,
    )
    return CalculoLeer(condiciones=condiciones, plan_cuotas=[a_cuota_plan(c) for c in plan])


def a_cuota_plan(c: calculos.Cuota) -> CuotaPlan:
    return CuotaPlan(
        numero=c.numero,
        vencimiento=c.vencimiento,
        capital=c.capital,
        interes=c.interes,
        cuota=c.cuota,
        saldo_despues=c.saldo_despues,
    )


def reprogramar_pendientes(
    plan: list[CuotaPlan], saldo: Decimal, condiciones: CondicionesContrato
) -> list[CuotaPlan]:
    """Conserva las cuotas pagadas y recalcula las pendientes con la misma cuota nivelada."""
    pagadas = [q for q in plan if q.estado == "pagada"]
    siguiente = len(pagadas) + 1
    nuevas = calculos.plan_cuota_fija(
        saldo,
        condiciones.cuota_nivelada,
        condiciones.tasa_interes_anual_pct,
        siguiente,
        calculos.sumar_meses(
            condiciones.fecha_primera_cuota, siguiente - 1, condiciones.dia_pago_mensual
        ),
        condiciones.dia_pago_mensual,
    )
    return pagadas + [a_cuota_plan(c) for c in nuevas]


def aplicar_saldo_inicial(calculo: CalculoLeer, inicial: SaldoInicial) -> list[CuotaPlan]:
    """Marca como pagadas las cuotas ya cubiertas en papel y ajusta el resto al saldo real."""
    cond = calculo.condiciones
    if inicial.saldo_capital > cond.saldo_a_pagar:
        raise ReglaNegocio(
            "El saldo actual no puede ser mayor que el saldo a pagar del contrato",
            campos={"saldo_inicial.saldo_capital": "excede_saldo"},
        )
    if inicial.cuotas_pagadas > cond.numero_cuotas:
        raise ReglaNegocio(
            "Las cuotas pagadas superan el número de cuotas del contrato",
            campos={"saldo_inicial.cuotas_pagadas": "excede_cuotas"},
        )
    plan = [q.model_copy() for q in calculo.plan_cuotas]
    for q in plan[: inicial.cuotas_pagadas]:
        q.marcar_pagada()
    esperado = (
        plan[inicial.cuotas_pagadas - 1].saldo_despues
        if inicial.cuotas_pagadas
        else cond.saldo_a_pagar
    )
    if inicial.saldo_capital == esperado:
        return plan
    return reprogramar_pendientes(plan, inicial.saldo_capital, cond)


async def crear(datos: ContratoCrear) -> Contrato:
    """Guarda cliente, reserva el lote y crea la promesa numerada, todo en una transacción."""
    calculo = calcular(datos.condiciones)
    plan = calculo.plan_cuotas
    saldo = calculo.condiciones.saldo_a_pagar
    if datos.saldo_inicial:
        plan = aplicar_saldo_inicial(calculo, datos.saldo_inicial)
        saldo = datos.saldo_inicial.saldo_capital

    async def _transaccion(session: AsyncClientSession) -> Contrato:
        cliente = await clientes_service.guardar_por_dpi(datos.comprador, session=session)
        lote = await reservar(datos.lote, datos.lotificacion, session=session)
        numero = await db.siguiente_correlativo("contrato", session=session)
        contrato = Contrato(
            numero=numero,
            fecha_firma=datos.fecha_firma,
            lotificacion=datos.lotificacion,
            cliente_id=cliente.id,
            lote_id=lote.id,
            comprador=datos.comprador,
            conyuge_gestor=datos.conyuge_gestor,
            dependientes=datos.dependientes,
            lote=datos.lote,
            condiciones=calculo.condiciones,
            plan_cuotas=plan,
            notario=datos.notario,
            saldo_inicial=datos.saldo_inicial,
            # quien viene del papel ya pagó su enganche
            total_pagado_enganche=calculo.condiciones.enganche if datos.saldo_inicial else CERO,
            total_pagado_capital=calculo.condiciones.saldo_a_pagar - saldo,
            saldo_capital=saldo,
            estado="vigente" if saldo > 0 else "cancelado_total",
        )
        await contrato.insert(session=session)
        lote.contrato_id = contrato.id
        if saldo == 0:
            lote.estado = "vendido"
        await lote.save(session=session)
        detalle = {"numero": numero, "con_saldo_inicial": datos.saldo_inicial is not None}
        await registrar("crear", "contratos", contrato.id, detalle, session=session)
        return contrato

    try:
        async with db.obtener_cliente().start_session() as session:
            return await session.with_transaction(_transaccion)
    except DuplicateKeyError as e:
        raise Conflicto(
            "Otro usuario registró el mismo lote o cliente al mismo tiempo; intente de nuevo"
        ) from e


async def obtener(contrato_id: PydanticObjectId, session=None) -> Contrato:
    contrato = await Contrato.get(contrato_id, session=session)
    if contrato is None or contrato.eliminado_en is not None:
        raise NoEncontrado("Promesa de compra-venta no encontrada")
    return contrato


async def eliminar(contrato_id: PydanticObjectId, motivo: str) -> EliminadoLeer:
    """Borrado lógico de la promesa y de todos sus recibos; el lote vuelve a estar disponible."""

    async def _transaccion(session: AsyncClientSession) -> EliminadoLeer:
        contrato = await obtener(contrato_id, session=session)
        momento = ahora()
        resultado = await Recibo.find(
            Recibo.contrato_id == contrato.id,
            Recibo.eliminado_en == None,  # noqa: E711
            session=session,
        ).update({"$set": {"eliminado_en": momento, "motivo_eliminacion": motivo}}, session=session)
        recibos = resultado.modified_count if resultado else 0
        lote = await Lote.get(contrato.lote_id, session=session)
        if lote and lote.contrato_id == contrato.id:
            lote.estado, lote.contrato_id, lote.actualizado_en = "disponible", None, momento
            await lote.save(session=session)
        contrato.eliminado_en, contrato.motivo_eliminacion = momento, motivo
        await contrato.save(session=session)
        detalle = {"numero": contrato.numero, "motivo": motivo, "recibos_eliminados": recibos}
        await registrar("eliminar", "contratos", contrato.id, detalle, session=session)
        return EliminadoLeer(
            id=str(contrato.id),
            numero_formateado=contrato.numero_formateado,
            recibos_eliminados=recibos,
        )

    async with db.obtener_cliente().start_session() as session:
        return await session.with_transaction(_transaccion)


async def buscar(
    texto: str | None, estado: str | None, pagina: int, tamano: int
) -> tuple[list[Contrato], int]:
    condiciones: list[dict] = [{"eliminado_en": None}]
    if texto and texto.strip():
        t = texto.strip()
        patron = re.escape(t)
        opciones: list[dict] = [
            {"comprador.nombres_apellidos": {"$regex": patron, "$options": "i"}},
            {"comprador.dpi": {"$regex": f"^{re.escape(t.replace(' ', ''))}"}},
            {"lote.codigo": {"$regex": patron, "$options": "i"}},
        ]
        if t.isdigit():
            opciones.append({"numero": int(t)})
        condiciones.append({"$or": opciones})
    if estado:
        condiciones.append({"estado": estado})
    consulta = Contrato.find({"$and": condiciones})
    total = await consulta.count()
    items = await consulta.sort("-numero").skip((pagina - 1) * tamano).limit(tamano).to_list()
    return items, total


def a_leer(c: Contrato) -> ContratoLeer:
    datos = c.model_dump(
        exclude={
            "id",
            "revision_id",
            "actualizado_en",
            "cliente_id",
            "lote_id",
            "eliminado_en",
            "motivo_eliminacion",
        }
    )
    return ContratoLeer(
        **datos,
        id=str(c.id),
        numero_formateado=c.numero_formateado,
        cliente_id=str(c.cliente_id),
        lote_id=str(c.lote_id),
    )


def a_resumen(c: Contrato) -> ContratoResumen:
    return ContratoResumen(
        id=str(c.id),
        numero=c.numero,
        numero_formateado=c.numero_formateado,
        fecha_firma=c.fecha_firma,
        comprador_nombre=c.comprador.nombres_apellidos,
        comprador_dpi=c.comprador.dpi,
        lotificacion=c.lotificacion,
        lote_codigo=c.lote.codigo,
        total=c.condiciones.total,
        saldo_capital=c.saldo_capital,
        estado=c.estado,
    )
