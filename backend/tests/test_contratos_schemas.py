"""Validaciones del formulario y cálculo (sin base de datos)."""

from decimal import Decimal as D

import pytest
from pydantic import ValidationError

from app.modules.contratos.schemas import ContratoCrear
from app.modules.contratos.service import calcular
from tests.datos import contrato_ejemplo


def test_contrato_ejemplo_es_valido_y_normaliza():
    c = ContratoCrear.model_validate(contrato_ejemplo())
    assert c.lote.codigo == "36-B34"  # mayúsculas
    assert c.comprador.nit == "12345679"  # sin guion


def test_calculo_reproduce_contrato_real():
    c = ContratoCrear.model_validate(contrato_ejemplo())
    r = calcular(c.condiciones)
    assert r.condiciones.total == D("122400.00")
    assert r.condiciones.saldo_a_pagar == D("112400.00")
    assert r.condiciones.cuota_nivelada == D("10219.00")
    assert r.condiciones.numero_cuotas == 11
    assert r.plan_cuotas[-1].cuota == D("10210.00")


def test_cuotas_por_defecto_son_plazo_por_12():
    datos = contrato_ejemplo(condiciones__numero_cuotas=None, condiciones__plazo_anios=4)
    r = calcular(ContratoCrear.model_validate(datos).condiciones)
    assert r.condiciones.numero_cuotas == 48
    assert len(r.plan_cuotas) == 48


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"comprador__dpi": "1234567882101"}, "DPI inválido"),
        ({"comprador__dpi": ""}, "DPI del comprador es obligatorio"),
        ({"comprador__nit": "1234567-8"}, "NIT inválido"),
        ({"condiciones__plazo_anios": 5}, "less than or equal to 4"),
        ({"condiciones__numero_cuotas": 13}, "máximo es 12 cuotas"),
        ({"condiciones__enganche_fraccionado": [{"fecha": "2025-01-22", "monto": "5000"}]},
         "suma del enganche fraccionado"),
        ({"condiciones__fecha_primera_cuota": "2025-01-01"}, "posterior a la fecha de firma"),
        ({"condiciones__precio_terreno": "-1"}, "greater than or equal to 0"),
        ({"condiciones__precio_terreno": "10.555"}, "decimal places"),
        ({"comprador__email": "no-es-correo"}, "pattern"),
        ({"lote__area_m2": "0"}, "greater than 0"),
    ],
)  # fmt: skip
def test_validaciones_del_formulario(cambios, mensaje):
    with pytest.raises(ValidationError, match=mensaje):
        ContratoCrear.model_validate(contrato_ejemplo(**cambios))
