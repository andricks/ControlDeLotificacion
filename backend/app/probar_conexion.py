"""Prueba la conexión a MongoDB Atlas sin mostrar la cadena de conexión.

Uso (desde backend/):  .venv\\Scripts\\python -m app.probar_conexion
"""

import asyncio
import sys

from pymongo import AsyncMongoClient
from pymongo.errors import (
    AutoReconnect,
    ConfigurationError,
    OperationFailure,
    ServerSelectionTimeoutError,
)

from app.core.config import obtener_settings


async def main() -> int:
    settings = obtener_settings()
    if not settings.mongodb_configurado:
        print("❌ MONGODB_URI no está configurado en el archivo .env de la raíz del proyecto.")
        return 1
    cliente = AsyncMongoClient(
        settings.mongodb_uri.get_secret_value(),  # type: ignore[union-attr]
        serverSelectionTimeoutMS=10000,
    )
    try:
        info = await cliente.server_info()
        colecciones = await cliente[settings.mongodb_db].list_collection_names()
        print(
            f"✅ Conexión correcta a MongoDB {info.get('version')} — base '{settings.mongodb_db}' "
            f"({len(colecciones)} colecciones)"
        )
        return 0
    except OperationFailure as e:
        if e.code == 18:
            print(
                "❌ Usuario o contraseña incorrectos "
                "(revisa MONGODB_URI y Database Access en Atlas)."
            )
        else:
            print(f"❌ MongoDB rechazó la operación (código {e.code}).")
        return 1
    except AutoReconnect as e:
        if "SSL" in str(e) or "TLS" in str(e):
            print(
                "❌ Atlas cerró la conexión segura (TLS). Casi siempre es porque tu IP pública "
                "no está en Atlas > Network Access (tu proveedor puede cambiarla entre conexiones)."
            )
        else:
            print("❌ Se perdió la conexión con el clúster; intenta de nuevo.")
        return 1
    except ServerSelectionTimeoutError:
        print(
            "❌ No se pudo alcanzar el clúster: agrega tu IP en Atlas > Network Access "
            "y revisa tu conexión a internet."
        )
        return 1
    except ConfigurationError:
        print(
            "❌ La cadena de conexión tiene un formato inválido. Si la contraseña tiene "
            "caracteres especiales (@ : / ? # %), cámbiala por una solo alfanumérica."
        )
        return 1
    finally:
        await cliente.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(asyncio.run(main()))
