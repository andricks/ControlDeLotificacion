"""Inicio de sesión exclusivo con Google, sesión en cookie, roles y gestión de usuarios."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core import seguridad
from app.core.config import obtener_settings
from app.core.errores import ErrorConfiguracion, NoAutenticado
from app.core.seguridad import COOKIE_SESION, IdentidadGoogle, verificar_token_google
from app.modules.auditoria.models import Auditoria
from app.modules.usuarios.models import Usuario
from tests.datos import contrato_ejemplo

CLIENT_ID = "cliente-prueba.apps.googleusercontent.com"
CLAVE_GOOGLE = rsa.generate_private_key(public_exponent=65537, key_size=2048)
CLAVE_AJENA = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class _JwksFalso:
    """Sustituye la descarga de llaves públicas de Google por una llave local."""

    def get_signing_key_from_jwt(self, _token):
        return type("Clave", (), {"key": CLAVE_GOOGLE.public_key()})()


def _token_google(clave=CLAVE_GOOGLE, **cambios) -> str:
    momento = datetime.now(UTC)
    datos = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "sub": "1234567890",
        "email": "Dueno@Gmail.com",
        "email_verified": True,
        "name": "Dueño Prueba",
        "picture": "https://lh3.googleusercontent.com/foto",
        "iat": momento,
        "exp": momento + timedelta(hours=1),
        **cambios,
    }
    return jwt.encode(datos, clave, algorithm="RS256")


@pytest.fixture
def google(monkeypatch):
    monkeypatch.setattr(seguridad, "_cliente_jwks", lambda: _JwksFalso())
    monkeypatch.setattr(obtener_settings(), "google_client_id", CLIENT_ID)
    monkeypatch.setattr(obtener_settings(), "admin_correos", "dueno@gmail.com")


# ---------- Verificación del token de Google (sin base de datos) ----------


async def test_token_google_valido_devuelve_identidad(google):
    identidad = await verificar_token_google(_token_google())
    assert identidad == IdentidadGoogle(
        sub="1234567890",
        correo="dueno@gmail.com",
        nombre="Dueño Prueba",
        foto="https://lh3.googleusercontent.com/foto",
    )


@pytest.mark.parametrize(
    ("clave", "cambios"),
    [
        (CLAVE_AJENA, {}),  # firma que no es de Google
        (CLAVE_GOOGLE, {"aud": "otra-app.apps.googleusercontent.com"}),
        (CLAVE_GOOGLE, {"iss": "https://evil.example.com"}),
        (CLAVE_GOOGLE, {"exp": datetime.now(UTC) - timedelta(hours=1)}),
        (CLAVE_GOOGLE, {"email_verified": False}),
    ],
    ids=["firma_ajena", "otra_audiencia", "otro_emisor", "expirado", "correo_sin_verificar"],
)
async def test_token_google_invalido_se_rechaza(google, clave, cambios):
    with pytest.raises(NoAutenticado):
        await verificar_token_google(_token_google(clave, **cambios))


async def test_sin_client_id_configurado_es_error_de_configuracion(google, monkeypatch):
    monkeypatch.setattr(obtener_settings(), "google_client_id", "")
    with pytest.raises(ErrorConfiguracion):
        await verificar_token_google(_token_google())


# ---------- Protección de endpoints (sin base de datos) ----------


@pytest.mark.parametrize(
    "ruta", ["/api/v1/contratos", "/api/v1/recibos", "/api/v1/cartera", "/api/v1/auth/yo"]
)
async def test_endpoints_exigen_sesion(cliente_http, ruta):
    r = await cliente_http.get(ruta)
    assert r.status_code == 401
    assert r.json()["codigo"] == "NO_AUTENTICADO"


async def test_cookie_falsificada_se_rechaza(cliente_http):
    falsa = jwt.encode(
        {"sub": "x", "iat": datetime.now(UTC), "exp": datetime.now(UTC) + timedelta(hours=1),
         "tipo": "sesion"},
        "otro-secreto-que-no-es-el-del-servidor-0123456789",
        algorithm="HS256",
    )  # fmt: skip
    cliente_http.cookies.set(COOKIE_SESION, falsa)
    assert (await cliente_http.get("/api/v1/contratos")).status_code == 401


async def test_config_publica_y_login_valida_cuerpo(cliente_http, google):
    r = await cliente_http.get("/api/v1/auth/config")
    assert r.json() == {"google_client_id": CLIENT_ID}
    assert (await cliente_http.post("/api/v1/auth/google", json={})).status_code == 422


async def test_login_con_token_invalido_401(cliente_http, google):
    r = await cliente_http.post(
        "/api/v1/auth/google", json={"credencial": _token_google(CLAVE_AJENA)}
    )
    assert r.status_code == 401
    assert COOKIE_SESION not in r.cookies


async def test_limite_de_intentos_de_login(cliente_http, google):
    cuerpo = {"credencial": _token_google(CLAVE_AJENA)}
    codigos = [(await cliente_http.post("/api/v1/auth/google", json=cuerpo)).status_code
               for _ in range(11)]  # fmt: skip
    assert codigos[:10] == [401] * 10
    assert codigos[10] == 429


# ---------- Flujo completo contra Atlas (facturas_test) ----------


@pytest.mark.atlas
async def test_admin_de_env_entra_y_obtiene_sesion(bd, cliente_http, google):
    r = await cliente_http.post("/api/v1/auth/google", json={"credencial": _token_google()})
    assert r.status_code == 200, r.text
    assert r.json()["correo"] == "dueno@gmail.com"
    assert r.json()["rol"] == "admin"
    cabecera = r.headers["set-cookie"].lower()
    assert "httponly" in cabecera and "samesite=strict" in cabecera

    yo = await cliente_http.get("/api/v1/auth/yo")
    assert yo.status_code == 200
    assert yo.json()["nombre"] == "Dueño Prueba"
    assert (await cliente_http.get("/api/v1/contratos")).status_code == 200

    usuario = await Usuario.find_one(Usuario.correo == "dueno@gmail.com")
    assert usuario.google_sub == "1234567890"
    assert await Auditoria.find_one(
        Auditoria.accion == "iniciar_sesion", Auditoria.usuario == "dueno@gmail.com"
    )

    assert (await cliente_http.post("/api/v1/auth/salir")).status_code == 204
    assert (await cliente_http.get("/api/v1/contratos")).status_code == 401


@pytest.mark.atlas
async def test_cuenta_no_autorizada_no_puede_entrar(bd, cliente_http, google):
    r = await cliente_http.post(
        "/api/v1/auth/google",
        json={"credencial": _token_google(email="intruso@gmail.com", sub="999")},
    )
    assert r.status_code == 403
    assert "no está autorizada" in r.json()["detalle"]
    assert await Usuario.find_one(Usuario.correo == "intruso@gmail.com") is None
    assert await Auditoria.find_one(
        Auditoria.accion == "inicio_sesion_rechazado", Auditoria.usuario == "intruso@gmail.com"
    )


@pytest.mark.atlas
async def test_cuenta_registrada_entra_con_su_rol_y_luego_desactivada_no(bd, cliente_http, google):
    await Usuario(correo="cajera@gmail.com", rol="operador").insert()
    token = _token_google(email="cajera@gmail.com", sub="555")
    r = await cliente_http.post("/api/v1/auth/google", json={"credencial": token})
    assert r.status_code == 200
    assert r.json()["rol"] == "operador"

    usuario = await Usuario.find_one(Usuario.correo == "cajera@gmail.com")
    usuario.activo = False
    await usuario.save()
    # La sesión ya emitida deja de servir de inmediato…
    assert (await cliente_http.get("/api/v1/contratos")).status_code == 401
    # …y no puede volver a entrar.
    r = await cliente_http.post("/api/v1/auth/google", json={"credencial": token})
    assert r.status_code == 403


@pytest.mark.atlas
async def test_misma_direccion_con_otra_cuenta_de_google_se_rechaza(bd, cliente_http, google):
    await Usuario(correo="cajera@gmail.com", rol="operador", google_sub="original").insert()
    token = _token_google(email="cajera@gmail.com", sub="otra-cuenta")
    r = await cliente_http.post("/api/v1/auth/google", json={"credencial": token})
    assert r.status_code == 403


@pytest.mark.atlas
async def test_rol_consulta_solo_lee(cliente_con_rol):
    consulta = await cliente_con_rol("consulta")
    assert (await consulta.get("/api/v1/contratos")).status_code == 200
    r = await consulta.post("/api/v1/contratos", json=contrato_ejemplo())
    assert r.status_code == 403
    assert r.json()["codigo"] == "SIN_PERMISO"


@pytest.mark.atlas
async def test_auditoria_registra_al_usuario_real(api):
    r = await api.post("/api/v1/contratos", json=contrato_ejemplo())
    assert r.status_code == 201, r.text
    registro = await Auditoria.find_one(Auditoria.coleccion == "contratos")
    assert registro.usuario == "admin@prueba.gt"


# ---------- Gestión de usuarios (solo admin) ----------


@pytest.mark.atlas
async def test_solo_admin_gestiona_usuarios(cliente_con_rol):
    operador = await cliente_con_rol("operador")
    assert (await operador.get("/api/v1/usuarios")).status_code == 403
    r = await operador.post("/api/v1/usuarios", json={"correo": "x@gmail.com"})
    assert r.status_code == 403


@pytest.mark.atlas
async def test_admin_autoriza_cambia_rol_y_desactiva(api):
    r = await api.post("/api/v1/usuarios", json={"correo": "Nuevo@Gmail.com", "rol": "operador"})
    assert r.status_code == 201, r.text
    nuevo = r.json()
    assert (nuevo["correo"], nuevo["rol"], nuevo["activo"]) == ("nuevo@gmail.com", "operador", True)

    duplicado = await api.post("/api/v1/usuarios", json={"correo": "nuevo@gmail.com"})
    assert duplicado.status_code == 409
    invalido = await api.post("/api/v1/usuarios", json={"correo": "no-es-correo"})
    assert invalido.status_code == 422

    r = await api.patch(f"/api/v1/usuarios/{nuevo['id']}", json={"rol": "consulta",
                                                                 "activo": False})  # fmt: skip
    assert (r.json()["rol"], r.json()["activo"]) == ("consulta", False)

    lista = (await api.get("/api/v1/usuarios")).json()
    assert {u["correo"] for u in lista} == {"admin@prueba.gt", "nuevo@gmail.com"}
    assert await Auditoria.find_one(
        Auditoria.accion == "actualizar_usuario", Auditoria.usuario == "admin@prueba.gt"
    )


@pytest.mark.atlas
async def test_admin_no_puede_quitarse_admin_ni_dejar_sin_admins(api):
    yo = (await api.get("/api/v1/auth/yo")).json()
    r = await api.patch(f"/api/v1/usuarios/{yo['id']}", json={"rol": "operador"})
    assert r.status_code == 422
    r = await api.patch(f"/api/v1/usuarios/{yo['id']}", json={"activo": False})
    assert r.status_code == 422


@pytest.mark.atlas
async def test_actualizar_usuario_inexistente_404(api):
    r = await api.patch("/api/v1/usuarios/650000000000000000000000", json={"rol": "admin"})
    assert r.status_code == 404


# ---------- Endurecimiento (revisión de seguridad) ----------


async def test_origen_ajeno_no_puede_modificar(cliente_http):
    r = await cliente_http.post(
        "/api/v1/auth/google",
        json={"credencial": "x" * 30},
        headers={"Origin": "https://sitio-malicioso.example"},
    )
    assert r.status_code == 403
    assert r.json()["detalle"] == "Origen no permitido"


def test_produccion_no_arranca_con_configuracion_insegura():
    from pydantic import SecretStr

    from app.core.config import Settings

    inseguro = Settings(entorno="produccion", jwt_secreto=SecretStr("solo-desarrollo-cambiar"))
    with pytest.raises(RuntimeError, match="JWT_SECRETO"):
        inseguro.validar_produccion()
    seguro = Settings(
        entorno="produccion",
        jwt_secreto=SecretStr("k" * 48),
        cookie_segura=True,
        cors_origenes="https://sistema.example.gt",
    )
    seguro.validar_produccion()


@pytest.mark.atlas
async def test_salir_revoca_tambien_cookies_copiadas(bd, cliente_http, google):
    r = await cliente_http.post("/api/v1/auth/google", json={"credencial": _token_google()})
    copiada = r.cookies[COOKIE_SESION]
    assert (await cliente_http.post("/api/v1/auth/salir")).status_code == 204
    cliente_http.cookies.set(COOKIE_SESION, copiada)
    r = await cliente_http.get("/api/v1/auth/yo")
    assert r.status_code == 401


@pytest.mark.atlas
async def test_cambiar_rol_revoca_la_sesion_abierta(api, cliente_con_rol):
    operador = await cliente_con_rol("operador")
    yo = (await operador.get("/api/v1/auth/yo")).json()
    r = await api.patch(f"/api/v1/usuarios/{yo['id']}", json={"rol": "consulta"})
    assert r.status_code == 200
    assert (await operador.get("/api/v1/contratos")).status_code == 401


@pytest.mark.atlas
async def test_admin_de_env_degradado_no_se_vuelve_a_promover(bd, cliente_http, google):
    token = _token_google()
    await cliente_http.post("/api/v1/auth/google", json={"credencial": token})
    usuario = await Usuario.find_one(Usuario.correo == "dueno@gmail.com")
    usuario.rol = "operador"
    await usuario.save()
    r = await cliente_http.post("/api/v1/auth/google", json={"credencial": token})
    assert r.json()["rol"] == "operador"
