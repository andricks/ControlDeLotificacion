from datetime import datetime

from beanie import Document
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.core.tipos import ahora
from app.modules.usuarios.schemas import Rol


class Usuario(Document):
    """Cuenta de Google autorizada. Sin contraseñas: Google autentica, el sistema autoriza."""

    correo: str  # en minúsculas
    nombre: str = ""
    foto: str | None = None
    rol: Rol = "consulta"
    activo: bool = True
    google_sub: str | None = None  # id estable de la cuenta de Google; se fija en el 1.er acceso
    sesion_version: int = 0  # se incrementa al salir / cambiar rol / desactivar → revoca sesiones
    ultimo_acceso: datetime | None = None
    creado_en: datetime = Field(default_factory=ahora)
    actualizado_en: datetime | None = None

    class Settings:
        name = "usuarios"
        indexes = [
            IndexModel([("correo", ASCENDING)], unique=True),
            # Parcial: varias cuentas aún sin primer acceso tienen google_sub = null.
            IndexModel(
                [("google_sub", ASCENDING)],
                name="google_sub_unico",
                unique=True,
                partialFilterExpression={"google_sub": {"$type": "string"}},
            ),
        ]
