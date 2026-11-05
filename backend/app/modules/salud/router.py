from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.core import db
from app.core.config import obtener_settings

router = APIRouter(prefix="/salud", tags=["salud"])


class EstadoSalud(BaseModel):
    estado: Literal["ok"]
    base_datos: Literal["conectada", "sin_configurar", "error"]


@router.get("", response_model=EstadoSalud, summary="Estado de la API y de la base de datos")
async def salud() -> EstadoSalud:
    if not obtener_settings().mongodb_configurado:
        return EstadoSalud(estado="ok", base_datos="sin_configurar")
    return EstadoSalud(estado="ok", base_datos="conectada" if await db.ping() else "error")
