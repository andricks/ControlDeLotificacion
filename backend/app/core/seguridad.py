"""Autenticación exclusiva con Google + sesión propia en cookie httpOnly (ver ADR-003).

Flujo: el frontend obtiene un ID token de Google → `POST /auth/google` lo verifica aquí
(firma RS256 con las llaves públicas de Google, audiencia = nuestro Client ID, emisor y
correo verificado) → el servicio decide si la cuenta está autorizada → se emite un JWT de
sesión (HS256, `JWT_SECRETO`) en una cookie httpOnly + SameSite=Strict.
"""

import asyncio
import time
from collections import defaultdict, deque
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated, Any

import jwt
from beanie import PydanticObjectId
from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import obtener_settings
from app.core.errores import (
    DemasiadosIntentos,
    ErrorConfiguracion,
    NoAutenticado,
    SinPermiso,
)
from app.core.tipos import ahora

COOKIE_SESION = "sesion"
GOOGLE_CERTS = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_EMISORES = ["https://accounts.google.com", "accounts.google.com"]
JERARQUIA = {"consulta": 0, "operador": 1, "admin": 2}
METODOS_LECTURA = {"GET", "HEAD", "OPTIONS"}

# Usuario de la petición en curso (lo usa auditoria.registrar sin pasarlo por cada servicio).
usuario_en_curso: ContextVar[str] = ContextVar("usuario_en_curso", default="sistema")

_jwks: jwt.PyJWKClient | None = None


@dataclass(frozen=True)
class IdentidadGoogle:
    sub: str
    correo: str
    nombre: str
    foto: str | None


def _cliente_jwks() -> jwt.PyJWKClient:
    global _jwks
    if _jwks is None:
        _jwks = jwt.PyJWKClient(GOOGLE_CERTS, cache_keys=True, lifespan=3600, timeout=10)
    return _jwks


def _decodificar_google(credencial: str, client_id: str) -> dict[str, Any]:
    clave = _cliente_jwks().get_signing_key_from_jwt(credencial)
    return jwt.decode(
        credencial,
        clave.key,
        algorithms=["RS256"],
        audience=client_id,
        issuer=GOOGLE_EMISORES,
        leeway=30,
        options={"require": ["exp", "iat", "iss", "aud", "sub"]},
    )


async def verificar_token_google(credencial: str) -> IdentidadGoogle:
    client_id = obtener_settings().google_client_id
    if not client_id:
        raise ErrorConfiguracion("GOOGLE_CLIENT_ID no está configurado en .env")
    try:
        datos = await asyncio.to_thread(_decodificar_google, credencial, client_id)
    except jwt.PyJWKClientConnectionError as exc:
        raise ErrorConfiguracion("No se pudo contactar a Google para verificar el acceso") from exc
    except (jwt.InvalidTokenError, jwt.PyJWKClientError) as exc:
        raise NoAutenticado("El inicio de sesión con Google no es válido o expiró") from exc
    correo = str(datos.get("email", "")).lower()
    if not correo or datos.get("email_verified") is not True:
        raise NoAutenticado("La cuenta de Google no tiene un correo verificado")
    return IdentidadGoogle(
        sub=str(datos["sub"]),
        correo=correo,
        nombre=str(datos.get("name") or correo),
        foto=datos.get("picture"),
    )


# ---------- Sesión propia ----------


def crear_token_sesion(usuario_id: str, correo: str, version: int = 0) -> str:
    """`version` = `Usuario.sesion_version`; al incrementarla se revocan todas sus sesiones."""
    s = obtener_settings()
    momento = ahora()
    return jwt.encode(
        {
            "sub": usuario_id,
            "correo": correo,
            "ver": version,
            "iat": momento,
            "exp": momento + timedelta(hours=s.sesion_horas),
            "tipo": "sesion",
        },
        s.jwt_secreto.get_secret_value(),
        algorithm="HS256",
    )


def leer_token_sesion(token: str) -> dict[str, Any]:
    try:
        datos = jwt.decode(
            token,
            obtener_settings().jwt_secreto.get_secret_value(),
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.InvalidTokenError as exc:
        raise NoAutenticado("Tu sesión expiró. Inicia sesión de nuevo con Google") from exc
    if datos.get("tipo") != "sesion":
        raise NoAutenticado("Sesión no válida")
    return datos


@dataclass(frozen=True)
class UsuarioSesion:
    id: str
    correo: str
    nombre: str
    rol: str


async def usuario_actual(request: Request) -> UsuarioSesion:
    """Exige una sesión válida y una cuenta todavía activa (la baja surte efecto inmediato)."""
    from app.modules.usuarios import repository  # import tardío: evita ciclo con modelos

    token = request.cookies.get(COOKIE_SESION)
    if not token:
        raise NoAutenticado("Inicia sesión con tu cuenta de Google")
    datos = leer_token_sesion(token)
    try:
        usuario_id = PydanticObjectId(datos["sub"])
    except Exception as exc:
        raise NoAutenticado("Sesión no válida") from exc
    usuario = await repository.por_id(usuario_id)
    if usuario is None or not usuario.activo:
        raise NoAutenticado("Tu cuenta ya no tiene acceso al sistema")
    if datos.get("ver") != usuario.sesion_version:
        raise NoAutenticado("Tu sesión fue cerrada. Inicia sesión de nuevo con Google")
    usuario_en_curso.set(usuario.correo)
    return UsuarioSesion(str(usuario.id), usuario.correo, usuario.nombre, usuario.rol)


UsuarioActual = Annotated[UsuarioSesion, Depends(usuario_actual)]


async def requiere_sesion(request: Request, usuario: UsuarioActual) -> UsuarioSesion:
    """Dependencia global de los módulos de negocio: rol `consulta` solo puede leer."""
    if request.method not in METODOS_LECTURA and usuario.rol == "consulta":
        raise SinPermiso("Tu rol es de solo consulta; no puedes modificar información")
    return usuario


def requiere_rol(rol_minimo: str):
    async def _verificar(usuario: UsuarioActual) -> UsuarioSesion:
        if JERARQUIA[usuario.rol] < JERARQUIA[rol_minimo]:
            raise SinPermiso("No tienes permiso para esta acción")
        return usuario

    return _verificar


# ---------- Defensa CSRF adicional a SameSite=Strict ----------


class OrigenPermitido:
    """Rechaza peticiones que modifican datos si traen un `Origin` que no es el del frontend."""

    def __init__(self, app: ASGIApp, origenes: list[str]) -> None:
        self.app = app
        self.origenes = set(origenes)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] not in METODOS_LECTURA:
            origen = Headers(scope=scope).get("origin")
            if origen and origen not in self.origenes:
                respuesta = JSONResponse(
                    status_code=403,
                    content={
                        "detalle": "Origen no permitido",
                        "codigo": "SIN_PERMISO",
                        "campos": {},
                    },
                )
                await respuesta(scope, receive, send)
                return
        await self.app(scope, receive, send)


# ---------- Límite de intentos de inicio de sesión (memoria del proceso) ----------


class LimitadorIntentos:
    def __init__(self, maximo: int, ventana_s: float) -> None:
        self.maximo = maximo
        self.ventana_s = ventana_s
        self._intentos: dict[str, deque[float]] = defaultdict(deque)

    def verificar(self, clave: str) -> None:
        ahora_s = time.monotonic()
        cola = self._intentos[clave]
        while cola and ahora_s - cola[0] > self.ventana_s:
            cola.popleft()
        if len(self._intentos) > 10_000:  # no crecer sin límite con IPs de un solo intento
            self._intentos = defaultdict(deque, {k: v for k, v in self._intentos.items() if v})
            cola = self._intentos[clave]
        if len(cola) >= self.maximo:
            raise DemasiadosIntentos("Demasiados intentos de inicio de sesión. Espera un minuto")
        cola.append(ahora_s)

    def reiniciar(self) -> None:
        self._intentos.clear()


limitador_login = LimitadorIntentos(maximo=10, ventana_s=60)
