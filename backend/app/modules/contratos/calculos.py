"""Cálculos de la promesa de compra-venta: totales y plan de cuotas niveladas.

Funciones puras (sin BD) para poder probarlas de forma aislada.
"""

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from app.core.errores import ReglaNegocio

CENTAVO = Decimal("0.01")
PLAZO_MIN_ANIOS = 1
PLAZO_MAX_ANIOS = 4
CUOTAS_MAX = PLAZO_MAX_ANIOS * 12


def redondear(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, ROUND_HALF_UP)


@dataclass(frozen=True)
class Totales:
    total: Decimal
    saldo_a_pagar: Decimal


def calcular_totales(
    precio_terreno: Decimal, mejoras: Decimal, enganche: Decimal, otros_descuentos: Decimal
) -> Totales:
    """total = precio + mejoras; saldo = total − enganche − descuentos."""
    for nombre, valor in {
        "precio_terreno": precio_terreno,
        "mejoras": mejoras,
        "enganche": enganche,
        "otros_descuentos": otros_descuentos,
    }.items():
        if valor < 0:
            raise ReglaNegocio("El monto no puede ser negativo", campos={nombre: "negativo"})
    total = redondear(precio_terreno + mejoras)
    saldo = redondear(total - enganche - otros_descuentos)
    if saldo < 0:
        raise ReglaNegocio(
            "El enganche y los descuentos superan el total", campos={"enganche": "excede_total"}
        )
    return Totales(total=total, saldo_a_pagar=saldo)


@dataclass(frozen=True)
class Cuota:
    numero: int
    vencimiento: date
    capital: Decimal
    interes: Decimal
    cuota: Decimal
    saldo_despues: Decimal


def sumar_meses(fecha: date, meses: int, dia: int) -> date:
    """Misma fecha `meses` después, usando `dia` y ajustando a fin de mes (30 → 28 feb)."""
    indice = fecha.month - 1 + meses
    anio, mes = fecha.year + indice // 12, indice % 12 + 1
    return date(anio, mes, min(dia, calendar.monthrange(anio, mes)[1]))


def cuota_sugerida(saldo: Decimal, numero_cuotas: int, tasa_anual_pct: Decimal) -> Decimal:
    """Cuota nivelada (sistema francés) redondeada hacia arriba al quetzal entero.

    Con tasa 0 es saldo / n. Ej.: 112,400 / 11 = 10,218.18 → 10,219.00.
    """
    if numero_cuotas <= 0:
        raise ReglaNegocio("El número de cuotas debe ser mayor que cero")
    i = tasa_anual_pct / Decimal(1200)
    exacta = saldo / numero_cuotas if i == 0 else saldo * i / (1 - (1 + i) ** -numero_cuotas)
    return exacta.quantize(Decimal("1"), ROUND_CEILING).quantize(CENTAVO)


def generar_plan(
    saldo: Decimal,
    numero_cuotas: int,
    tasa_anual_pct: Decimal,
    fecha_primera_cuota: date,
    dia_pago: int,
    cuota: Decimal | None = None,
) -> list[Cuota]:
    """Plan de cuotas niveladas; la última cuota se ajusta para cerrar el saldo exacto."""
    if not 1 <= numero_cuotas <= CUOTAS_MAX:
        raise ReglaNegocio(
            f"El número de cuotas debe estar entre 1 y {CUOTAS_MAX}",
            campos={"numero_cuotas": "fuera_de_rango"},
        )
    if not 1 <= dia_pago <= 31:
        raise ReglaNegocio(
            "El día de pago debe estar entre 1 y 31", campos={"dia_pago": "invalido"}
        )
    if tasa_anual_pct < 0:
        raise ReglaNegocio("La tasa de interés no puede ser negativa")
    if saldo <= 0:
        return []

    cuota = cuota if cuota is not None else cuota_sugerida(saldo, numero_cuotas, tasa_anual_pct)
    i = tasa_anual_pct / Decimal(1200)
    plan: list[Cuota] = []
    pendiente = saldo
    for n in range(1, numero_cuotas + 1):
        interes = redondear(pendiente * i)
        es_ultima = n == numero_cuotas
        capital = pendiente if es_ultima else redondear(cuota - interes)
        if capital <= 0:
            raise ReglaNegocio(
                "La cuota no alcanza a cubrir los intereses", campos={"cuota": "insuficiente"}
            )
        if not es_ultima and capital >= pendiente:
            raise ReglaNegocio(
                f"Con esa cuota el saldo se cancela en la cuota {n}, antes de las {numero_cuotas} "
                "pactadas; reduzca la cuota o el número de cuotas",
                campos={"cuota": "excesiva"},
            )
        pendiente = redondear(pendiente - capital)
        plan.append(
            Cuota(
                numero=n,
                vencimiento=sumar_meses(fecha_primera_cuota, n - 1, dia_pago),
                capital=capital,
                interes=interes,
                cuota=redondear(capital + interes),
                saldo_despues=pendiente,
            )
        )
    return plan


def plan_cuota_fija(
    saldo: Decimal,
    cuota: Decimal,
    tasa_anual_pct: Decimal,
    numero_inicial: int,
    fecha_inicial: date,
    dia_pago: int,
) -> list[Cuota]:
    """Reprograma un saldo manteniendo la cuota: el plazo se acorta.

    Se usa tras un abono a capital ("reducir el plazo ... pero no modificar la cuota") y al
    cargar clientes existentes con su saldo actual.
    """
    i = tasa_anual_pct / Decimal(1200)
    plan: list[Cuota] = []
    pendiente = redondear(saldo)
    while pendiente > 0:
        if len(plan) >= CUOTAS_MAX:
            raise ReglaNegocio(
                "Con esa cuota el saldo no se cancela dentro del plazo máximo de 4 años",
                campos={"cuota": "insuficiente"},
            )
        interes = redondear(pendiente * i)
        capital = min(pendiente, redondear(cuota - interes))
        if capital <= 0:
            raise ReglaNegocio(
                "La cuota no alcanza a cubrir los intereses", campos={"cuota": "insuficiente"}
            )
        pendiente = redondear(pendiente - capital)
        k = len(plan)
        plan.append(
            Cuota(
                numero=numero_inicial + k,
                vencimiento=sumar_meses(fecha_inicial, k, dia_pago),
                capital=capital,
                interes=interes,
                cuota=redondear(capital + interes),
                saldo_despues=pendiente,
            )
        )
    return plan


def mora_sugerida(
    cuota: Decimal,
    vencimiento: date,
    fecha_pago: date,
    dias_gracia: int,
    pct_mensual: Decimal,
) -> tuple[int, Decimal]:
    """(días de atraso, recargo) — 5 % mensual por cada mes (o fracción) de atraso.

    Dentro de los días de gracia no hay recargo. Es una sugerencia: el cajero puede ajustarla.
    """
    dias = (fecha_pago - vencimiento).days
    if dias <= dias_gracia:
        return max(dias, 0), Decimal("0.00")
    meses = 1 + (dias - 1) // 30
    return dias, redondear(cuota * pct_mensual / 100 * meses)
