"""Datos de personas tal como aparecen en la Promesa de Compra Venta."""

from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.core.tipos import DineroPositivo, Email, Nombre, Texto, TextoCorto
from app.core.validaciones import dpi_valido, nit_valido, normalizar_dpi, normalizar_nit


def validar_dpi_opcional(valor: str | None) -> str | None:
    if valor is None or not valor.strip():
        return None
    dpi = normalizar_dpi(valor)
    if not dpi_valido(dpi):
        raise ValueError("DPI inválido: deben ser 13 dígitos con verificador correcto")
    return dpi


class PersonaDatos(BaseModel):
    """Cónyuge, familiar o gestor."""

    nombres_apellidos: Nombre
    dpi: str | None = None
    direccion: Texto | None = None
    telefono: TextoCorto | None = None
    email: Email | None = None
    fecha_nacimiento: date | None = None
    nacionalidad: TextoCorto = "Guatemalteca"
    profesion_actividad: Texto | None = None

    @field_validator("dpi")
    @classmethod
    def _dpi(cls, v: str | None) -> str | None:
        return validar_dpi_opcional(v)

    @field_validator("fecha_nacimiento")
    @classmethod
    def _nacimiento(cls, v: date | None) -> date | None:
        if v and v >= date.today():
            raise ValueError("La fecha de nacimiento debe ser anterior a hoy")
        return v


class TrabajoDatos(BaseModel):
    empresa: Texto | None = None
    direccion: Texto | None = None
    telefono: TextoCorto | None = None
    puesto: Texto | None = None
    tiempo_trabajo: TextoCorto | None = None
    ingreso_mensual: DineroPositivo | None = None
    otros_ingresos: DineroPositivo | None = None


class ClienteDatos(PersonaDatos):
    """Promitente comprador."""

    dpi: str  # obligatorio para el comprador
    nit: TextoCorto | None = None
    estado_civil: TextoCorto | None = None
    num_dependientes: int = Field(default=0, ge=0, le=20)
    trabajo: TrabajoDatos = Field(default_factory=TrabajoDatos)

    @field_validator("dpi")
    @classmethod
    def _dpi_obligatorio(cls, v: str) -> str:
        dpi = validar_dpi_opcional(v)
        if dpi is None:
            raise ValueError("El DPI del comprador es obligatorio")
        return dpi

    @field_validator("nit")
    @classmethod
    def _nit(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        if not nit_valido(v):
            raise ValueError("NIT inválido (dígito verificador incorrecto); use CF si no tiene")
        return normalizar_nit(v)


class ClienteLeer(ClienteDatos):
    id: str
