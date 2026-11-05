from datetime import date
from decimal import Decimal as D

import pytest

from app.core.errores import ReglaNegocio
from app.modules.contratos.calculos import mora_sugerida, plan_cuota_fija


@pytest.mark.parametrize(
    ("pago", "dias", "mora"),
    [
        (date(2025, 10, 30), 0, D("0.00")),  # a tiempo
        (date(2025, 11, 4), 5, D("0.00")),  # recibo real: 5 días de gracia
        (date(2025, 11, 5), 6, D("510.95")),  # 1 mes → 5 % de 10,219
        (date(2025, 11, 29), 30, D("510.95")),
        (date(2025, 11, 30), 31, D("1021.90")),  # 2 meses
        (date(2025, 10, 1), 0, D("0.00")),  # pago adelantado
    ],
)
def test_mora_sugerida(pago, dias, mora):
    assert mora_sugerida(D("10219.00"), date(2025, 10, 30), pago, 5, D("5")) == (dias, mora)


def test_reprogramar_tras_abono_mantiene_cuota_y_acorta_plazo():
    # tras la cuota 9 (saldo 20,429) el cliente abona 5,000 → saldo 15,429
    plan = plan_cuota_fija(D("15429.00"), D("10219.00"), D("0"), 10, date(2025, 11, 30), 30)
    assert [c.numero for c in plan] == [10, 11]
    assert plan[0].cuota == D("10219.00")
    assert plan[1].cuota == D("5210.00")
    assert plan[1].vencimiento == date(2025, 12, 30)
    assert plan[-1].saldo_despues == D("0.00")


def test_reprogramar_con_interes_cierra_en_cero():
    plan = plan_cuota_fija(D("50000"), D("2500"), D("12"), 5, date(2026, 1, 15), 15)
    assert plan[-1].saldo_despues == D("0.00")
    assert sum(c.capital for c in plan) == D("50000.00")
    assert all(c.cuota == D("2500.00") for c in plan[:-1])


def test_reprogramar_saldo_cero_no_genera_cuotas():
    assert plan_cuota_fija(D("0"), D("100"), D("0"), 1, date(2026, 1, 1), 1) == []


def test_reprogramar_cuota_que_no_cubre_intereses_falla():
    with pytest.raises(ReglaNegocio):
        plan_cuota_fija(D("100000"), D("500"), D("12"), 1, date(2026, 1, 1), 1)
