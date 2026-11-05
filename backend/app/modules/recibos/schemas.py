"""Recibo de Caja: entrada del formulario y respuestas de la API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.core.tipos import CERO, Dinero, DineroPositivo, Texto, TextoCorto
from app.modules.lotes.schemas import Lotificacion

Concepto = Literal["enganche", "cuota", "abono_capital", "otros"]
TextoObligatorio = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)
]


class Boleta(BaseModel):
    """Boleta de depósito relacionada (número / cuenta)."""

    numero: TextoObligatorio
    cuenta: TextoCorto | None = None


class Desglose(BaseModel):
    enganche: DineroPositivo = CERO
    capital: DineroPositivo = CERO
    intereses: DineroPositivo = CERO
    recargo_mora: DineroPositivo = CERO
    abono_capital: DineroPositivo = CERO
    otros: DineroPositivo = CERO

    @property
    def total(self) -> Decimal:
        return (
            self.enganche
            + self.capital
            + self.intereses
            + self.recargo_mora
            + self.abono_capital
            + self.otros
        )

    @property
    def reduce_saldo(self) -> Decimal:
        """Solo capital y abono a capital reducen el saldo (intereses y mora no)."""
        return self.capital + self.abono_capital


class ReciboCrear(BaseModel):
    contrato_id: str
    fecha: date
    concepto: Concepto
    cuota_numero: int | None = Field(default=None, ge=1, le=48)
    desglose: Desglose
    boletas: list[Boleta] = Field(default_factory=list, max_length=5)
    numero_fel: TextoCorto | None = None  # opcional, sin relación ni validación
    observaciones: Texto | None = None

    @model_validator(mode="after")
    def _coherencia(self) -> "ReciboCrear":
        d = self.desglose
        if d.total <= 0:
            raise ValueError("El total del recibo debe ser mayor que cero")
        if self.fecha > date.today():
            raise ValueError("La fecha del recibo no puede ser futura")
        if self.concepto == "cuota":
            if self.cuota_numero is None:
                raise ValueError("Indique el número de cuota que se paga")
            if d.capital + d.intereses <= 0:
                raise ValueError("Un pago de cuota debe incluir capital o intereses")
            if d.enganche:
                raise ValueError("El enganche se registra en un recibo aparte")
        else:
            if self.cuota_numero is not None:
                raise ValueError("El número de cuota solo aplica al concepto 'cuota'")
            if d.capital or d.intereses:
                raise ValueError("Capital e intereses solo aplican al pago de una cuota")
        if self.concepto == "enganche" and d.enganche <= 0:
            raise ValueError("Indique el monto del enganche")
        if self.concepto != "enganche" and d.enganche:
            raise ValueError("El monto de enganche solo aplica al concepto 'enganche'")
        if self.concepto == "abono_capital" and d.abono_capital <= 0:
            raise ValueError("Indique el monto del abono a capital")
        if self.concepto in ("enganche", "otros") and d.abono_capital:
            raise ValueError(
                "El abono a capital se registra con concepto 'abono_capital' o 'cuota'"
            )
        return self


class ReciboAnular(BaseModel):
    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=250)]


class SugerenciaPago(BaseModel):
    """Lo que el sistema propone para el siguiente recibo (el cajero puede ajustarlo)."""

    contrato_id: str
    fecha: date
    saldo_capital: Dinero
    enganche_pendiente: Dinero
    cuota_numero: int | None
    cuota_mes: str | None
    vencimiento: date | None
    capital: Dinero
    intereses: Dinero
    dias_atraso: int
    recargo_mora: Dinero
    total_sugerido: Dinero
    cuotas_vencidas: int


class ReciboLeer(BaseModel):
    id: str
    numero: int
    numero_formateado: str
    numero_fel: str | None
    lugar: str
    fecha: date
    contrato_id: str
    contrato_numero: int
    cliente_id: str
    cliente_nombre: str
    lotificacion: Lotificacion | None = None
    lotes_texto: str
    concepto: Concepto
    cuota_numero: int | None
    cuota_mes: str | None
    desglose: Desglose
    total: Dinero
    total_en_letras: str
    saldo_anterior: Dinero
    saldo_actual: Dinero
    boletas: list[Boleta]
    observaciones: str | None
    anulado: bool
    motivo_anulacion: str | None
    anulado_en: datetime | None
    creado_en: datetime
