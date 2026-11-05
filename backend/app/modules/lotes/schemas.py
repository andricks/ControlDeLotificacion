from typing import Annotated, Literal

from beanie import DecimalAnnotation
from pydantic import BaseModel, Field, StringConstraints

from app.core.tipos import TextoCorto

Lotificacion = Literal["monaco", "finca_el_ensueno", "tablon_campestre2"]

# Nombre que se imprime en el encabezado de la promesa, recibos y estado de cuenta.
LOTIFICACIONES: dict[str, str] = {
    "monaco": 'LOTIFICACIÓN "MONACO"',
    "finca_el_ensueno": 'LOTIFICACIÓN "FINCA EL ENSUEÑO"',
    "tablon_campestre2": 'LOTIFICACIÓN "TABLON CAMPESTRE2"',
}


def nombre_lotificacion(clave: str | None, por_defecto: str) -> str:
    """Las promesas creadas antes de poder elegir lotificación usan el nombre de configuración."""
    return LOTIFICACIONES[clave] if clave else por_defecto


CodigoLote = Annotated[
    str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=30)
]


class LoteDatos(BaseModel):
    """Identificación del inmueble según la Promesa de Compra Venta."""

    codigo: CodigoLote  # "36-B34"
    area_m2: Annotated[DecimalAnnotation, Field(gt=0, max_digits=12, decimal_places=2)]
    finca: TextoCorto | None = None
    folio: TextoCorto | None = None
    libro: TextoCorto | None = None
    libro_de: TextoCorto | None = None  # departamento del registro, p. ej. "Jalapa"
