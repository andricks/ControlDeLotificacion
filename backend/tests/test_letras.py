from decimal import Decimal

import pytest

from app.core.letras import monto_a_letras


@pytest.mark.parametrize(
    ("monto", "esperado"),
    [
        ("10219.00", "DIEZ MIL DOSCIENTOS DIECINUEVE QUETZALES"),  # recibo real
        ("1", "UN QUETZAL"),
        ("0", "CERO QUETZALES"),
        ("21", "VEINTIÚN QUETZALES"),
        ("31", "TREINTA Y UN QUETZALES"),
        ("100", "CIEN QUETZALES"),
        ("101", "CIENTO UN QUETZALES"),
        ("1000", "MIL QUETZALES"),
        ("21000", "VEINTIÚN MIL QUETZALES"),
        ("122400", "CIENTO VEINTIDÓS MIL CUATROCIENTOS QUETZALES"),
        ("1000000", "UN MILLÓN DE QUETZALES"),
        ("2500000", "DOS MILLONES QUINIENTOS MIL QUETZALES"),
        ("1500.50", "MIL QUINIENTOS QUETZALES CON 50/100"),
        ("75.05", "SETENTA Y CINCO QUETZALES CON 05/100"),
    ],
)
def test_monto_a_letras(monto, esperado):
    assert monto_a_letras(Decimal(monto)) == esperado


def test_monto_negativo_falla():
    with pytest.raises(ValueError):
        monto_a_letras(Decimal("-1"))
