from datetime import datetime
from typing import Literal

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field

from app.core.tipos import Email

Rol = Literal["admin", "operador", "consulta"]


class LoginGoogle(BaseModel):
    """ID token (JWT) que entrega el botón de Google Identity Services."""

    credencial: str = Field(min_length=20, max_length=4096)


class ConfigAuth(BaseModel):
    google_client_id: str


class UsuarioLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PydanticObjectId
    correo: str
    nombre: str
    foto: str | None
    rol: Rol
    activo: bool
    ultimo_acceso: datetime | None
    creado_en: datetime


class UsuarioCrear(BaseModel):
    """Autoriza una cuenta de Google para entrar al sistema."""

    correo: Email
    rol: Rol = "consulta"


class UsuarioActualizar(BaseModel):
    rol: Rol | None = None
    activo: bool | None = None
