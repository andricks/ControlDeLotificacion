from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.core.tipos import CERO, Dinero, ahora
from app.modules.clientes.schemas import ClienteDatos, PersonaDatos
from app.modules.contratos.schemas import (
    CondicionesContrato,
    CuotaPlan,
    DependienteDatos,
    EstadoContrato,
    NotarioDatos,
    SaldoInicial,
)
from app.modules.lotes.schemas import LoteDatos, Lotificacion


class Contrato(Document):
    """Promesa de Compra Venta. `comprador` y `lote` son la instantánea al momento de firmar."""

    numero: int
    fecha_firma: date
    # None = promesa anterior a poder elegir lotificación (el PDF usa la de configuración).
    lotificacion: Lotificacion | None = None
    cliente_id: PydanticObjectId
    lote_id: PydanticObjectId
    comprador: ClienteDatos
    conyuge_gestor: PersonaDatos | None = None
    dependientes: list[DependienteDatos] = Field(default_factory=list)
    lote: LoteDatos
    condiciones: CondicionesContrato
    plan_cuotas: list[CuotaPlan]
    notario: NotarioDatos | None = None
    saldo_inicial: SaldoInicial | None = None
    total_pagado_enganche: Dinero = CERO
    total_pagado_capital: Dinero = CERO
    saldo_capital: Dinero
    estado: EstadoContrato = "vigente"
    creado_en: datetime = Field(default_factory=ahora)
    actualizado_en: datetime | None = None
    # Borrado lógico: el documento legal se conserva pero deja de aparecer en el sistema.
    eliminado_en: datetime | None = None
    motivo_eliminacion: str | None = None

    @property
    def numero_formateado(self) -> str:
        return f"{self.numero:05d}"

    class Settings:
        name = "contratos"
        indexes = [
            IndexModel([("numero", DESCENDING)], unique=True),
            IndexModel([("cliente_id", ASCENDING)]),
            IndexModel([("lote_id", ASCENDING)]),
            IndexModel([("estado", ASCENDING)]),
            IndexModel([("comprador.dpi", ASCENDING)]),
        ]
