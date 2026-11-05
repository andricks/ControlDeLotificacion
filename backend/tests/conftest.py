import pytest
from httpx import ASGITransport, AsyncClient

from app.core import db
from app.core.config import obtener_settings
from app.core.seguridad import COOKIE_SESION, crear_token_sesion, limitador_login
from app.main import crear_app
from app.modules.usuarios.models import Usuario


@pytest.fixture
async def cliente_http():
    """Cliente HTTP contra la app, sin ejecutar el lifespan (no conecta a Atlas)."""
    async with AsyncClient(
        transport=ASGITransport(app=crear_app()), base_url="http://prueba"
    ) as cliente:
        yield cliente


@pytest.fixture
async def bd():
    """Conecta a la base de PRUEBAS (facturas_test) y la deja vacía antes de cada test."""
    settings = obtener_settings()
    nombre = settings.mongodb_db_test
    assert nombre.endswith("_test") and nombre != settings.mongodb_db, "Nunca limpiar la base real"
    base = await db.conectar(settings, nombre_db=nombre)
    for coleccion in await base.list_collection_names():
        await base[coleccion].delete_many({})
    yield base
    await db.desconectar()


@pytest.fixture(autouse=True)
def _reiniciar_limitador():
    limitador_login.reiniciar()


@pytest.fixture
async def cliente_con_rol(bd):
    """Fábrica: cliente HTTP con sesión iniciada como un usuario real del rol indicado."""
    abiertos: list[AsyncClient] = []

    async def _crear(rol: str = "admin", correo: str | None = None) -> AsyncClient:
        usuario = Usuario(correo=correo or f"{rol}@prueba.gt", nombre=f"Prueba {rol}", rol=rol)
        await usuario.insert()
        cliente = AsyncClient(transport=ASGITransport(app=crear_app()), base_url="http://prueba")
        cliente.cookies.set(COOKIE_SESION, crear_token_sesion(str(usuario.id), usuario.correo))
        abiertos.append(cliente)
        return cliente

    yield _crear
    for c in abiertos:
        await c.aclose()


@pytest.fixture
async def api(cliente_con_rol):
    """Cliente HTTP autenticado como administrador, con la base de pruebas conectada."""
    return await cliente_con_rol("admin")


def pytest_collection_modifyitems(config, items):
    if obtener_settings().mongodb_configurado:
        return
    omitir = pytest.mark.skip(reason="MONGODB_URI no configurado en .env")
    for item in items:
        if "atlas" in item.keywords:
            item.add_marker(omitir)
