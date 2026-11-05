from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Request, Response, status

from app.core.config import obtener_settings
from app.core.seguridad import (
    COOKIE_SESION,
    UsuarioActual,
    UsuarioSesion,
    crear_token_sesion,
    limitador_login,
    requiere_rol,
    verificar_token_google,
)
from app.modules.usuarios import service
from app.modules.usuarios.schemas import (
    ConfigAuth,
    LoginGoogle,
    UsuarioActualizar,
    UsuarioCrear,
    UsuarioLeer,
)

auth_router = APIRouter(prefix="/auth", tags=["autenticación"])
usuarios_router = APIRouter(prefix="/usuarios", tags=["usuarios"])

Admin = Annotated[UsuarioSesion, Depends(requiere_rol("admin"))]


def _poner_cookie(respuesta: Response, token: str) -> None:
    s = obtener_settings()
    respuesta.set_cookie(
        COOKIE_SESION,
        token,
        max_age=s.sesion_horas * 3600,
        httponly=True,
        secure=s.cookie_segura,
        samesite="strict",
        path="/api",
    )


@auth_router.get("/config", response_model=ConfigAuth, summary="Client ID público de Google")
async def config() -> ConfigAuth:
    return ConfigAuth(google_client_id=obtener_settings().google_client_id)


@auth_router.post(
    "/google",
    response_model=UsuarioLeer,
    summary="Iniciar sesión con la cuenta de Google (único método de acceso)",
)
async def login_google(datos: LoginGoogle, request: Request, respuesta: Response) -> UsuarioLeer:
    limitador_login.verificar(request.client.host if request.client else "desconocido")
    identidad = await verificar_token_google(datos.credencial)
    usuario = await service.iniciar_sesion_google(identidad)
    _poner_cookie(
        respuesta, crear_token_sesion(str(usuario.id), usuario.correo, usuario.sesion_version)
    )
    respuesta.headers["Cache-Control"] = "no-store"
    return UsuarioLeer.model_validate(usuario)


@auth_router.get("/yo", response_model=UsuarioLeer, summary="Usuario de la sesión actual")
async def yo(usuario: UsuarioActual) -> UsuarioLeer:
    return UsuarioLeer.model_validate(await service.obtener(usuario.id))


@auth_router.post(
    "/salir", status_code=status.HTTP_204_NO_CONTENT, summary="Cerrar la sesión actual"
)
async def salir(usuario: UsuarioActual, respuesta: Response) -> None:
    await service.cerrar_sesion(usuario)
    respuesta.delete_cookie(COOKIE_SESION, path="/api")


@usuarios_router.get(
    "", response_model=list[UsuarioLeer], summary="Cuentas de Google autorizadas (solo admin)"
)
async def listar(_: Admin) -> list[UsuarioLeer]:
    return [UsuarioLeer.model_validate(u) for u in await service.listar()]


@usuarios_router.post(
    "",
    response_model=UsuarioLeer,
    status_code=status.HTTP_201_CREATED,
    summary="Autorizar una cuenta de Google (solo admin)",
)
async def autorizar(datos: UsuarioCrear, _: Admin) -> UsuarioLeer:
    return UsuarioLeer.model_validate(await service.autorizar(datos))


@usuarios_router.patch(
    "/{usuario_id}",
    response_model=UsuarioLeer,
    summary="Cambiar rol o activar/desactivar una cuenta (solo admin)",
)
async def actualizar(
    usuario_id: PydanticObjectId, datos: UsuarioActualizar, actor: Admin
) -> UsuarioLeer:
    return UsuarioLeer.model_validate(await service.actualizar(usuario_id, datos, actor))
