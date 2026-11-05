from datetime import datetime

from beanie import Document
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.core.tipos import ahora
from app.modules.clientes.schemas import ClienteDatos


class Cliente(Document, ClienteDatos):
    creado_en: datetime = Field(default_factory=ahora)
    actualizado_en: datetime | None = None

    class Settings:
        name = "clientes"
        indexes = [
            IndexModel([("dpi", ASCENDING)], unique=True),
            IndexModel([("nombres_apellidos", ASCENDING)]),
        ]
