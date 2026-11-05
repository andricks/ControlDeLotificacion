"""Conexión a MongoDB Atlas e inicialización de Beanie."""

import logging

from beanie import Document, init_beanie
from pymongo import AsyncMongoClient, ReturnDocument
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import Settings
from app.core.errores import ErrorConfiguracion

log = logging.getLogger(__name__)


def _modelos() -> list[type[Document]]:
    """Modelos Beanie de todos los módulos (import tardío para evitar ciclos)."""
    from app.modules.auditoria.models import Auditoria
    from app.modules.clientes.models import Cliente
    from app.modules.configuracion.models import Configuracion
    from app.modules.contratos.models import Contrato
    from app.modules.lotes.models import Lote
    from app.modules.recibos.models import Recibo
    from app.modules.usuarios.models import Usuario

    return [Auditoria, Cliente, Configuracion, Contrato, Lote, Recibo, Usuario]


_cliente: AsyncMongoClient | None = None
_db: AsyncDatabase | None = None


async def conectar(settings: Settings, nombre_db: str | None = None) -> AsyncDatabase:
    global _cliente, _db
    if not settings.mongodb_configurado:
        raise ErrorConfiguracion("MONGODB_URI no está configurado en .env")
    _cliente = AsyncMongoClient(
        settings.mongodb_uri.get_secret_value(),  # type: ignore[union-attr]
        tz_aware=True,
        uuidRepresentation="standard",
        # Atlas puede tardar >10 s en descubrir el primario desde algunas redes.
        serverSelectionTimeoutMS=30000,
    )
    _db = _cliente[nombre_db or settings.mongodb_db]
    await init_beanie(database=_db, document_models=_modelos())
    log.info("Conectado a MongoDB, base '%s'", _db.name)
    return _db


async def desconectar() -> None:
    global _cliente, _db
    if _cliente is not None:
        await _cliente.close()
    _cliente, _db = None, None


def obtener_db() -> AsyncDatabase:
    if _db is None:
        raise ErrorConfiguracion("La base de datos no está conectada")
    return _db


def obtener_cliente() -> AsyncMongoClient:
    if _cliente is None:
        raise ErrorConfiguracion("La base de datos no está conectada")
    return _cliente


async def ping() -> bool:
    if _db is None:
        return False
    try:
        await _db.command("ping")
        return True
    except Exception:  # la salud solo informa el estado, no propaga
        log.exception("Ping a MongoDB falló")
        return False


async def siguiente_correlativo(nombre: str, session: AsyncClientSession | None = None) -> int:
    """Número correlativo atómico (contrato, recibo); nunca contar documentos para numerar."""
    doc = await obtener_db()["contadores"].find_one_and_update(
        {"_id": nombre},
        {"$inc": {"valor": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
        session=session,
    )
    return int(doc["valor"])
