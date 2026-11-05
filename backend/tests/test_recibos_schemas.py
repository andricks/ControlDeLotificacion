import pytest
from pydantic import ValidationError

from app.modules.recibos.schemas import ReciboCrear

BASE = {"contrato_id": "a" * 24, "fecha": "2025-11-04"}


def recibo(concepto, desglose, **extra):
    return ReciboCrear.model_validate({**BASE, "concepto": concepto, "desglose": desglose, **extra})


def test_recibo_de_cuota_valido():
    r = recibo("cuota", {"capital": "10219.00"}, cuota_numero=9, numero_fel="2540")
    assert r.desglose.total == r.desglose.reduce_saldo


@pytest.mark.parametrize(
    ("concepto", "desglose", "extra", "mensaje"),
    [
        ("cuota", {"capital": "100"}, {}, "número de cuota"),
        ("cuota", {"recargo_mora": "10"}, {"cuota_numero": 1}, "capital o intereses"),
        ("abono_capital", {"capital": "100", "abono_capital": "2000"}, {}, "solo aplican"),
        ("enganche", {"otros": "5"}, {}, "monto del enganche"),
        ("otros", {"enganche": "5"}, {}, "solo aplica al concepto 'enganche'"),
        ("otros", {"otros": "0"}, {}, "mayor que cero"),
        ("abono_capital", {"otros": "5"}, {}, "monto del abono"),
        ("otros", {"otros": "5"}, {"cuota_numero": 3}, "solo aplica al concepto 'cuota'"),
        ("otros", {"otros": "5"}, {"fecha": "2999-01-01"}, "no puede ser futura"),
        ("cuota", {"capital": "-1"}, {"cuota_numero": 1}, "greater than or equal to 0"),
    ],
)
def test_validaciones_recibo(concepto, desglose, extra, mensaje):
    with pytest.raises(ValidationError, match=mensaje):
        recibo(concepto, desglose, **extra)
