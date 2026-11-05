"""Errores de dominio y su traducción a respuestas HTTP."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ErrorDominio(Exception):
    status = 400
    codigo = "ERROR"

    def __init__(self, detalle: str, codigo: str | None = None, campos: dict | None = None):
        super().__init__(detalle)
        self.detalle = detalle
        self.codigo = codigo or self.codigo
        self.campos = campos or {}


class NoEncontrado(ErrorDominio):
    status = 404
    codigo = "NO_ENCONTRADO"


class ReglaNegocio(ErrorDominio):
    status = 422
    codigo = "REGLA_NEGOCIO"


class Conflicto(ErrorDominio):
    status = 409
    codigo = "CONFLICTO"


class NoAutenticado(ErrorDominio):
    status = 401
    codigo = "NO_AUTENTICADO"


class DemasiadosIntentos(ErrorDominio):
    status = 429
    codigo = "DEMASIADOS_INTENTOS"


class SinPermiso(ErrorDominio):
    status = 403
    codigo = "SIN_PERMISO"


class ErrorConfiguracion(ErrorDominio):
    status = 503
    codigo = "CONFIGURACION"


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorDominio)
    async def _manejar(_: Request, exc: ErrorDominio) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content={"detalle": exc.detalle, "codigo": exc.codigo, "campos": exc.campos},
        )
