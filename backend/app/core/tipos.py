"""Tipos compartidos por schemas y modelos."""

from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated

from beanie import DecimalAnnotation
from pydantic import BaseModel, Field, StringConstraints

# Dinero: Decimal en Python, Decimal128 en MongoDB, string en JSON. Máx. 2 decimales.
Dinero = Annotated[DecimalAnnotation, Field(max_digits=14, decimal_places=2)]
DineroPositivo = Annotated[DecimalAnnotation, Field(ge=0, max_digits=14, decimal_places=2)]
Porcentaje = Annotated[DecimalAnnotation, Field(ge=0, le=100, max_digits=6, decimal_places=2)]

Texto = Annotated[str, StringConstraints(strip_whitespace=True, max_length=250)]
TextoCorto = Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)]
Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=150)]
Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_lower=True, max_length=150, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    ),
]

CERO = Decimal("0.00")

# Guatemala no usa horario de verano: UTC−6 fijo (evita depender del paquete tzdata en Windows).
GUATEMALA = timezone(timedelta(hours=-6), "America/Guatemala")


def ahora() -> datetime:
    return datetime.now(UTC)


def hoy_guatemala() -> date:
    return datetime.now(GUATEMALA).date()


class Pagina[T](BaseModel):
    items: list[T]
    total: int
    pagina: int
    tamano: int
