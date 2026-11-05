from beanie import PydanticObjectId

from app.modules.usuarios.models import Usuario


async def por_correo(correo: str) -> Usuario | None:
    return await Usuario.find_one(Usuario.correo == correo.lower())


async def por_id(usuario_id: PydanticObjectId) -> Usuario | None:
    return await Usuario.get(usuario_id)


async def listar() -> list[Usuario]:
    return await Usuario.find_all().sort(+Usuario.correo).to_list()


async def contar_admins_activos() -> int:
    return await Usuario.find(Usuario.rol == "admin", Usuario.activo == True).count()  # noqa: E712
