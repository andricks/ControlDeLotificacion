from datetime import date
from decimal import Decimal as D

import pytest

from app.core.errores import ReglaNegocio
from app.modules.contratos.calculos import (
    calcular_totales,
    cuota_sugerida,
    generar_plan,
    sumar_meses,
)


def test_totales_contrato_real():
    t = calcular_totales(D("20000.00"), D("102400.00"), D("10000.00"), D("0.00"))
    assert t.total == D("122400.00")
    assert t.saldo_a_pagar == D("112400.00")


def test_enganche_mayor_al_total_falla():
    with pytest.raises(ReglaNegocio):
        calcular_totales(D("1000"), D("0"), D("2000"), D("0"))


def test_monto_negativo_falla():
    with pytest.raises(ReglaNegocio):
        calcular_totales(D("-1"), D("0"), D("0"), D("0"))


def test_cuota_sugerida_sin_interes_redondea_al_quetzal_hacia_arriba():
    assert cuota_sugerida(D("112400.00"), 11, D("0")) == D("10219.00")


def test_plan_contrato_real_coincide_con_recibo():
    plan = generar_plan(D("112400.00"), 11, D("0"), date(2025, 2, 28), dia_pago=30)
    assert len(plan) == 11
    assert all(c.cuota == D("10219.00") for c in plan[:10])
    assert plan[-1].cuota == D("10210.00")  # última ajustada
    assert sum(c.capital for c in plan) == D("112400.00")
    assert plan[7].saldo_despues == D("30648.00")  # saldo anterior del recibo cuota 9
    assert plan[8].saldo_despues == D("20429.00")  # saldo actual del recibo cuota 9
    assert plan[8].vencimiento == date(2025, 10, 30)  # cuota 9 = octubre
    assert plan[0].vencimiento == date(2025, 2, 28)
    assert plan[1].vencimiento == date(2025, 3, 30)  # vuelve al día 30
    assert plan[-1].saldo_despues == D("0.00")


@pytest.mark.parametrize("anios", [1, 2, 3, 4])
def test_plan_con_interes_cierra_en_cero(anios):
    plan = generar_plan(D("112400.00"), anios * 12, D("12"), date(2025, 2, 28), dia_pago=28)
    assert len(plan) == anios * 12
    assert plan[-1].saldo_despues == D("0.00")
    assert sum(c.capital for c in plan) == D("112400.00")
    assert plan[0].interes == D("1124.00")  # 1 % mensual del saldo inicial
    assert all(c.cuota == plan[0].cuota for c in plan[:-1])


def test_mas_de_4_anios_falla():
    with pytest.raises(ReglaNegocio):
        generar_plan(D("1000"), 49, D("0"), date(2025, 1, 1), dia_pago=1)


def test_cuota_excesiva_falla():
    with pytest.raises(ReglaNegocio):
        generar_plan(D("1000"), 12, D("0"), date(2025, 1, 1), dia_pago=1, cuota=D("600"))


def test_cuota_que_no_cubre_intereses_falla():
    with pytest.raises(ReglaNegocio):
        generar_plan(D("100000"), 12, D("24"), date(2025, 1, 1), dia_pago=1, cuota=D("1000"))


def test_saldo_cero_no_genera_cuotas():
    assert generar_plan(D("0"), 12, D("0"), date(2025, 1, 1), dia_pago=1) == []


def test_sumar_meses_ajusta_fin_de_mes_y_anio():
    assert sumar_meses(date(2025, 1, 31), 1, 31) == date(2025, 2, 28)
    assert sumar_meses(date(2024, 1, 31), 1, 31) == date(2024, 2, 29)
    assert sumar_meses(date(2025, 11, 30), 2, 30) == date(2026, 1, 30)
