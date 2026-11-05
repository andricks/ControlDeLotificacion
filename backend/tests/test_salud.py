import pytest

from app.core import db
from app.core.config import obtener_settings


async def test_salud_responde_ok(cliente_http):
    r = await cliente_http.get("/api/v1/salud")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"
    assert r.json()["base_datos"] in {"conectada", "sin_configurar", "error"}


@pytest.mark.atlas
async def test_conexion_real_atlas_y_correlativo():
    settings = obtener_settings()
    base = await db.conectar(settings, nombre_db=settings.mongodb_db_test)
    try:
        assert await db.ping()
        await base["contadores"].delete_one({"_id": "prueba"})
        assert await db.siguiente_correlativo("prueba") == 1
        assert await db.siguiente_correlativo("prueba") == 2
    finally:
        await base["contadores"].delete_one({"_id": "prueba"})
        await db.desconectar()
