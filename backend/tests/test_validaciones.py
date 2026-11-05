"""Números ficticios (no pertenecen a personas reales) con verificador válido."""

import pytest

from app.core.validaciones import dpi_valido, nit_valido

DPI_FICTICIO_1 = "1234567892101"  # verificador 9, depto 21 (Jalapa), municipio 01
DPI_FICTICIO_2 = "8765432122101"  # verificador 2


@pytest.mark.parametrize("nit", ["576937-K", "576937k", "1234567-9", "CF", "cf", "12345679"])
def test_nit_valido(nit):
    assert nit_valido(nit)


@pytest.mark.parametrize("nit", ["1234567-8", "", "K", "12A45-6", "12345678"])
def test_nit_invalido(nit):
    assert not nit_valido(nit)


@pytest.mark.parametrize("dpi", [DPI_FICTICIO_1, DPI_FICTICIO_2, "1234 56789 2101"])
def test_dpi_valido(dpi):
    assert dpi_valido(dpi)


@pytest.mark.parametrize(
    "dpi",
    [
        "1234567882101",  # dígito verificador alterado
        "1234567892301",  # departamento 23 no existe
        "1234567892100",  # municipio 00
        "123456789210",  # 12 dígitos
        "12345678921AB",
    ],
)
def test_dpi_invalido(dpi):
    assert not dpi_valido(dpi)
