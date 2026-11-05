"""Cartera de cobro: situación de pago de cada promesa vigente."""

from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.core.tipos import Dinero
from app.modules.lotes.schemas import Lotificacion

# moroso: cuota vencida pasados los días de gracia · en_gracia: vencida dentro de la gracia
# por_vencer: vence en los próximos días de aviso (incluye hoy) · al_dia: nada pendiente cercano
SituacionPago = Literal["moroso", "en_gracia", "por_vencer", "al_dia"]


class ClienteCartera(BaseModel):
    contrato_id: str
    numero_formateado: str
    cliente_nombre: str
    telefono: str | None
    lotificacion: Lotificacion | None
    lote_codigo: str
    dia_pago_mensual: int
    cuota_nivelada: Dinero
    numero_cuotas: int
    cuotas_pagadas: int
    proxima_cuota_numero: int | None
    proxima_vencimiento: date | None
    proxima_monto: Dinero
    cuotas_vencidas: int
    dias_atraso: int
    monto_vencido: Dinero
    mora_estimada: Dinero
    enganche_pendiente: Dinero
    saldo_capital: Dinero
    ultimo_pago: date | None
    situacion: SituacionPago
    # Cláusula del contrato: dos o más cuotas en mora permiten rescindir la promesa.
    riesgo_rescision: bool


class ResumenCartera(BaseModel):
    clientes: int
    morosos: int
    en_gracia: int
    por_vencer: int
    al_dia: int
    riesgo_rescision: int
    monto_vencido: Dinero
    mora_estimada: Dinero


class CarteraLeer(BaseModel):
    fecha: date
    dias_gracia: int
    resumen: ResumenCartera
    items: list[ClienteCartera]
    total: int
    pagina: int
    tamano: int
