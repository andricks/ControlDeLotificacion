"""Formatos de presentación para PDFs (moneda, fechas en español, edad)."""

from datetime import date
from decimal import Decimal

from app.core.letras import entero_a_letras

MESES = [
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
]


def moneda(valor: Decimal | None, simbolo: str = "Q") -> str:
    if valor is None:
        return ""
    return f"{simbolo} {Decimal(valor):,.2f}"


def numero(valor: Decimal | None) -> str:
    return "" if valor is None else f"{Decimal(valor):,.2f}"


def fecha_corta(valor: date | None) -> str:
    return valor.strftime("%d/%m/%Y") if valor else ""


def mes_nombre(valor: date) -> str:
    return MESES[valor.month - 1]


def anio_en_letras(anio: int) -> str:
    """2025 → 'DOS MIL VEINTICINCO'."""
    return entero_a_letras(anio)


def edad(nacimiento: date | None, referencia: date) -> int | None:
    if nacimiento is None:
        return None
    return (
        referencia.year
        - nacimiento.year
        - ((referencia.month, referencia.day) < (nacimiento.month, nacimiento.day))
    )
