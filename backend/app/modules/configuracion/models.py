"""Datos del emisor y reglas del negocio que aparecen en los PDFs (documento único)."""

from decimal import Decimal

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel

from app.core.tipos import DineroPositivo, Porcentaje


class ReglasNegocio(BaseModel):
    dias_gracia: int = 5
    mora_pct_mensual: Porcentaje = Decimal("5.00")
    abono_capital_minimo: DineroPositivo = Decimal("2000.00")
    arras_pct_precio: Porcentaje = Decimal("20.00")
    arras_pct_pagado: Porcentaje = Decimal("50.00")


class CuentaBancaria(BaseModel):
    banco: str
    tipo: str
    numero: str
    titular: str


def _cuentas_por_defecto() -> list[CuentaBancaria]:
    titular = "ANDRICK SAUL ESTRADA AGUILAR"
    return [
        CuentaBancaria(banco="BANRURAL", tipo="AHORRO", numero="4269194666", titular=titular),
        CuentaBancaria(banco="BANCO INDUSTRIAL", tipo="AHORRO", numero="4516652", titular=titular),
    ]


class ConfiguracionDatos(BaseModel):
    empresa: str = "INMOBILIARIA ESTRADA"
    proyecto: str = 'LOTIFICACIÓN "TABLON CAMPESTRE2"'
    direccion_oficinas: str = "San Pedro Pinula, Jalapa, Kilómetro 124.5, Residenciales Monaco"
    telefono_oficinas: str = "5381-4009"
    direccion_proyecto: str = "San Pedro Pinula, Jalapa, Kilómetro 124.5, Residenciales Monaco"
    ciudad_documentos: str = "Jalapa"
    representante_legal: str = ""
    cuentas_bancarias: list[CuentaBancaria] = Field(default_factory=_cuentas_por_defecto)
    reglas: ReglasNegocio = Field(default_factory=ReglasNegocio)
    # El texto de las condiciones vive en `textos.py` (se edita ahí, no se copia a la BD).
    condiciones_generales_validadas: bool = False


class Configuracion(Document, ConfiguracionDatos):
    clave: str = "principal"

    class Settings:
        name = "configuracion"
        indexes = [IndexModel([("clave", ASCENDING)], unique=True)]


async def obtener_configuracion() -> Configuracion:
    """Devuelve la configuración; la crea con los valores por defecto la primera vez."""
    config = await Configuracion.find_one(Configuracion.clave == "principal")
    if config is None:
        config = await Configuracion().insert()
    return config
