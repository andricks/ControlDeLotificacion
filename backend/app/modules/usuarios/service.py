"""Reglas de acceso: Google autentica; aquí se decide quién está autorizado y con qué rol."""

import logging

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.core.config import obtener_settings
from app.core.errores import Conflicto, NoEncontrado, ReglaNegocio, SinPermiso
from app.core.seguridad import IdentidadGoogle, UsuarioSesion
from app.core.tipos import ahora
from app.modules.auditoria.models import registrar
from app.modules.usuarios import repository
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import UsuarioActualizar, UsuarioCrear

log = logging.getLogger(__name__)

MENSAJE_NO_AUTORIZADO = (
    "Tu cuenta de Google no está autorizada para entrar al sistema. "
    "Pide a un administrador que la agregue."
)


async def _rechazar(motivo: str, correo: str) -> None:
    # Estos registros caducan a los 90 días (índice TTL en auditoria). Si la auditoría falla,
    # el rechazo se mantiene: nunca se convierte en acceso ni en un 500.
    try:
        await registrar(
            "inicio_sesion_rechazado", "usuarios", None, {"motivo": motivo}, usuario=correo
        )
    except Exception:
        log.exception("No se pudo auditar un inicio de sesión rechazado")
    raise SinPermiso(MENSAJE_NO_AUTORIZADO)


async def iniciar_sesion_google(identidad: IdentidadGoogle) -> Usuario:
    """Devuelve el usuario autorizado o lanza SinPermiso. Nunca crea cuentas a cualquiera."""
    es_admin_env = identidad.correo in obtener_settings().lista_admin_correos
    usuario = await repository.por_correo(identidad.correo)

    if usuario is None:
        if not es_admin_env:
            await _rechazar("cuenta_no_registrada", identidad.correo)
        usuario = Usuario(correo=identidad.correo, rol="admin")
        log.info("Administrador inicial creado desde ADMIN_CORREOS")
    elif not usuario.activo:
        await _rechazar("cuenta_desactivada", identidad.correo)
    elif usuario.google_sub and usuario.google_sub != identidad.sub:
        # El correo ahora pertenece a otra cuenta de Google (p. ej. cuenta recreada).
        await _rechazar("cuenta_google_distinta", identidad.correo)

    # ADMIN_CORREOS solo crea el admin inicial; después manda lo que diga la colección `usuarios`.
    usuario.google_sub = identidad.sub
    usuario.nombre = identidad.nombre
    usuario.foto = identidad.foto
    usuario.ultimo_acceso = ahora()
    await usuario.save()
    await registrar("iniciar_sesion", "usuarios", usuario.id, usuario=usuario.correo)
    return usuario


async def cerrar_sesion(usuario: UsuarioSesion) -> None:
    """Revoca TODAS las sesiones de la cuenta (también cookies copiadas a otro equipo)."""
    await Usuario.find_one(Usuario.id == PydanticObjectId(usuario.id)).inc(
        {Usuario.sesion_version: 1}
    )
    await registrar(
        "cerrar_sesion", "usuarios", PydanticObjectId(usuario.id), usuario=usuario.correo
    )


async def obtener(usuario_id: str) -> Usuario:
    usuario = await repository.por_id(PydanticObjectId(usuario_id))
    if usuario is None:
        raise NoEncontrado("Usuario no encontrado")
    return usuario


async def listar() -> list[Usuario]:
    return await repository.listar()


async def autorizar(datos: UsuarioCrear) -> Usuario:
    if await repository.por_correo(datos.correo):
        raise Conflicto("Esa cuenta ya está registrada", campos={"correo": True})
    usuario = Usuario(correo=datos.correo, rol=datos.rol)
    try:
        await usuario.insert()
    except DuplicateKeyError as exc:
        raise Conflicto("Esa cuenta ya está registrada", campos={"correo": True}) from exc
    await registrar("autorizar_usuario", "usuarios", usuario.id, {"rol": datos.rol})
    return usuario


async def actualizar(usuario_id: PydanticObjectId, datos: UsuarioActualizar, actor: UsuarioSesion):
    usuario = await repository.por_id(usuario_id)
    if usuario is None:
        raise NoEncontrado("Usuario no encontrado")
    cambios = datos.model_dump(exclude_none=True)
    if not cambios:
        return usuario
    pierde_admin = usuario.rol == "admin" and (
        cambios.get("rol", "admin") != "admin" or cambios.get("activo") is False
    )
    if pierde_admin:
        if str(usuario.id) == actor.id:
            raise ReglaNegocio("No puedes quitarte el rol de administrador ni desactivarte")
        if await repository.contar_admins_activos() <= 1:
            raise ReglaNegocio("Debe quedar al menos un administrador activo")
    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    usuario.sesion_version += 1  # nuevo rol o baja: las sesiones abiertas dejan de valer
    usuario.actualizado_en = ahora()
    await usuario.save()
    await registrar("actualizar_usuario", "usuarios", usuario.id, cambios)
    return usuario
