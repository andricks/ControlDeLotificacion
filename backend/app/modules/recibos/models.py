from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.core.tipos import Dinero, ahora
from app.modules.contratos.schemas import CuotaPlan, EstadoContrato
from app.modules.lotes.schemas import Lotificacion
from app.modules.recibos.schemas import Boleta, Concepto, Desglose


class Recibo(Document):
    numero: int
    numero_fel: str | None = None
    lugar: str
    fecha: date
    contrato_id: PydanticObjectId
    contrato_numero: int
    cliente_id: PydanticObjectId
    cliente_nombre: str
    lotificacion: Lotificacion | None = None  # copiada de la promesa
    lotes_texto: str
    concepto: Concepto
    cuota_numero: int | None = None
    cuota_mes: str | None = None
    desglose: Desglose
    total: Dinero
    total_en_letras: str
    saldo_anterior: Dinero
    saldo_actual: Dinero
    boletas: list[Boleta] = Field(default_factory=list)
    observaciones: str | None = None
    anulado: bool = False
    motivo_anulacion: str | None = None
    anulado_en: datetime | None = None
    # Borrado lógico: el documento legal se conserva pero deja de aparecer en el sistema.
    eliminado_en: datetime | None = None
    motivo_eliminacion: str | None = None
    creado_en: datetime = Field(default_factory=ahora)
    # Estado del contrato antes de este recibo: permite anularlo de forma exacta.
    plan_anterior: list[CuotaPlan]
    estado_contrato_anterior: EstadoContrato

    @property
    def numero_formateado(self) -> str:
        return f"{self.numero:06d}"

    class Settings:
        name = "recibos"
        indexes = [
            IndexModel([("numero", DESCENDING)], unique=True),
            IndexModel([("contrato_id", ASCENDING), ("numero", DESCENDING)]),
            IndexModel([("cliente_id", ASCENDING)]),
            IndexModel([("fecha", DESCENDING)]),
        ]
