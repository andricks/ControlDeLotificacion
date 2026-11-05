"""Promesa de Compra Venta: entrada del formulario y respuestas de la API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from beanie import DecimalAnnotation
from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from app.core.tipos import CERO, Dinero, DineroPositivo, Nombre, Porcentaje, Texto, TextoCorto
from app.modules.clientes.schemas import ClienteDatos, PersonaDatos, validar_dpi_opcional
from app.modules.lotes.schemas import LoteDatos, Lotificacion

MontoPositivo = Annotated[DecimalAnnotation, Field(gt=0, max_digits=14, decimal_places=2)]
EstadoContrato = Literal["vigente", "cancelado_total", "desistido", "anulado"]


class EngancheFraccion(BaseModel):
    fecha: date
    monto: MontoPositivo


class DependienteDatos(BaseModel):
    nombre: Nombre
    edad: int | None = Field(default=None, ge=0, le=120)
    dpi: str | None = None

    @field_validator("dpi")
    @classmethod
    def _dpi(cls, v: str | None) -> str | None:
        return validar_dpi_opcional(v)


class NotarioDatos(BaseModel):
    """Legalización de firmas (opcional; en el papel suele quedar en blanco)."""

    ciudad: TextoCorto | None = None
    fecha: date | None = None
    nombre: Texto | None = None
    representante: Texto | None = None


class CondicionesEntrada(BaseModel):
    precio_terreno: DineroPositivo
    mejoras: DineroPositivo = CERO
    enganche: DineroPositivo = CERO
    otros_descuentos: DineroPositivo = CERO
    enganche_fraccionado: list[EngancheFraccion] = Field(default_factory=list, max_length=4)
    plazo_anios: int = Field(ge=1, le=4)
    numero_cuotas: int | None = Field(default=None, ge=1, le=48)
    tasa_interes_anual_pct: Porcentaje = CERO
    cuota_nivelada: MontoPositivo | None = None  # vacío = la calcula el sistema
    fecha_primera_cuota: date
    dia_pago_mensual: int | None = Field(default=None, ge=1, le=31)
    otras_condiciones: Annotated[str, Field(max_length=1000)] | None = None

    @model_validator(mode="after")
    def _coherencia(self) -> "CondicionesEntrada":
        maximo = self.plazo_anios * 12
        if self.numero_cuotas is not None and self.numero_cuotas > maximo:
            raise ValueError(f"Con {self.plazo_anios} año(s) de plazo el máximo es {maximo} cuotas")
        if self.enganche_fraccionado:
            suma = sum((f.monto for f in self.enganche_fraccionado), Decimal("0"))
            if suma != self.enganche:
                raise ValueError(
                    f"La suma del enganche fraccionado ({suma:,.2f}) debe ser igual al "
                    f"enganche ({self.enganche:,.2f})"
                )
        return self


class CondicionesContrato(CondicionesEntrada):
    """Condiciones con los valores calculados por el sistema."""

    total: Dinero
    saldo_a_pagar: Dinero
    numero_cuotas: int
    cuota_nivelada: Dinero
    dia_pago_mensual: int


class CuotaPlan(BaseModel):
    numero: int
    vencimiento: date
    capital: Dinero
    interes: Dinero
    cuota: Dinero
    saldo_despues: Dinero
    capital_pagado: Dinero = CERO
    interes_pagado: Dinero = CERO
    estado: Literal["pendiente", "parcial", "pagada"] = "pendiente"

    @property
    def capital_pendiente(self) -> Decimal:
        return self.capital - self.capital_pagado

    @property
    def interes_pendiente(self) -> Decimal:
        return self.interes - self.interes_pagado

    def marcar_pagada(self) -> None:
        self.capital_pagado, self.interes_pagado, self.estado = self.capital, self.interes, "pagada"


class SaldoInicial(BaseModel):
    """Clientes que ya venían pagando en papel: se registra solo su saldo actual."""

    saldo_capital: DineroPositivo
    cuotas_pagadas: int = Field(ge=0, le=48)
    fecha_corte: date
    nota: Texto | None = None


class ContratoCrear(BaseModel):
    fecha_firma: date
    lotificacion: Lotificacion
    comprador: ClienteDatos
    conyuge_gestor: PersonaDatos | None = None
    dependientes: list[DependienteDatos] = Field(default_factory=list, max_length=5)
    lote: LoteDatos
    condiciones: CondicionesEntrada
    notario: NotarioDatos | None = None
    saldo_inicial: SaldoInicial | None = None  # solo para contratos que vienen del papel

    @model_validator(mode="after")
    def _fechas(self) -> "ContratoCrear":
        if self.condiciones.fecha_primera_cuota <= self.fecha_firma:
            raise ValueError("La primera cuota debe ser posterior a la fecha de firma")
        return self


class CalculoEntrada(BaseModel):
    condiciones: CondicionesEntrada


class CalculoLeer(BaseModel):
    condiciones: CondicionesContrato
    plan_cuotas: list[CuotaPlan]


class ContratoLeer(BaseModel):
    id: str
    numero: int
    numero_formateado: str
    fecha_firma: date
    lotificacion: Lotificacion | None = None
    cliente_id: str
    lote_id: str
    comprador: ClienteDatos
    conyuge_gestor: PersonaDatos | None
    dependientes: list[DependienteDatos]
    lote: LoteDatos
    condiciones: CondicionesContrato
    plan_cuotas: list[CuotaPlan]
    notario: NotarioDatos | None
    saldo_inicial: SaldoInicial | None = None
    total_pagado_enganche: Dinero = CERO
    total_pagado_capital: Dinero
    saldo_capital: Dinero
    estado: EstadoContrato
    creado_en: datetime


class Eliminar(BaseModel):
    """Motivo obligatorio para borrar una promesa o un recibo (queda en auditoría)."""

    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=250)]


class EliminadoLeer(BaseModel):
    id: str
    numero_formateado: str
    recibos_eliminados: int = 0


class ContratoResumen(BaseModel):
    id: str
    numero: int
    numero_formateado: str
    fecha_firma: date
    comprador_nombre: str
    comprador_dpi: str
    lotificacion: Lotificacion | None = None
    lote_codigo: str
    total: Dinero
    saldo_capital: Dinero
    estado: EstadoContrato
