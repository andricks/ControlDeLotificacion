"""Punto de entrada de la API: uvicorn app.main:app --reload"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import db
from app.core.config import obtener_settings
from app.core.errores import registrar_manejadores
from app.core.seguridad import OrigenPermitido, requiere_sesion
from app.modules.cartera.router import router as cartera_router
from app.modules.clientes.router import router as clientes_router
from app.modules.contratos.router import router as contratos_router
from app.modules.recibos.router import router as recibos_router
from app.modules.salud.router import router as salud_router
from app.modules.usuarios.router import auth_router, usuarios_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = obtener_settings()
    if settings.mongodb_configurado:
        await db.conectar(settings)
    else:
        log.warning("MONGODB_URI no configurado: la API arranca sin base de datos")
    if not settings.google_client_id:
        log.warning("GOOGLE_CLIENT_ID no configurado: nadie podrá iniciar sesión")
    if not settings.lista_admin_correos:
        log.warning("ADMIN_CORREOS vacío: solo entran cuentas ya registradas en 'usuarios'")
    if settings.secreto_debil:
        log.warning("JWT_SECRETO débil o por defecto: cámbialo en .env (32+ caracteres)")
    yield
    await db.desconectar()


def crear_app() -> FastAPI:
    settings = obtener_settings()
    settings.validar_produccion()
    produccion = settings.entorno == "produccion"
    app = FastAPI(
        title="Sistema Documental — Promesas de compra-venta y recibos",
        version="0.1.0",
        lifespan=lifespan,
        # En producción no se publica el mapa de la API.
        docs_url=None if produccion else "/docs",
        redoc_url=None if produccion else "/redoc",
        openapi_url=None if produccion else "/openapi.json",
    )
    app.add_middleware(OrigenPermitido, origenes=settings.lista_cors)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.lista_cors,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type"],
        expose_headers=["Content-Disposition"],
    )
    registrar_manejadores(app)
    # Públicos: salud y autenticación. Todo lo demás exige sesión iniciada con Google.
    for r in (salud_router, auth_router, usuarios_router):
        app.include_router(r, prefix="/api/v1")
    for r in (clientes_router, contratos_router, recibos_router, cartera_router):
        app.include_router(r, prefix="/api/v1", dependencies=[Depends(requiere_sesion)])
    return app


app = crear_app()
