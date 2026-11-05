"""Configuración de la aplicación, leída desde `.env` (raíz del proyecto o backend/)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
RAIZ_BACKEND = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(RAIZ_PROYECTO / ".env", RAIZ_BACKEND / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: SecretStr | None = None
    mongodb_db: str = "facturas"
    mongodb_db_test: str = "facturas_test"

    jwt_secreto: SecretStr = SecretStr("solo-desarrollo-cambiar")
    # Inicio de sesión exclusivamente con Google (ver ADR-003)
    google_client_id: str = ""
    admin_correos: str = ""  # correos que siempre pueden entrar como admin (separados por coma)
    sesion_horas: int = 8
    cookie_segura: bool = False  # True en producción (HTTPS)
    entorno: Literal["desarrollo", "produccion"] = "desarrollo"

    @property
    def secreto_debil(self) -> bool:
        valor = self.jwt_secreto.get_secret_value()
        return len(valor) < 32 or "cambiar" in valor or "escribe-aqui" in valor

    def validar_produccion(self) -> None:
        """En producción no se arranca con configuración insegura."""
        if self.entorno != "produccion":
            return
        problemas = []
        if self.secreto_debil:
            problemas.append("JWT_SECRETO débil o por defecto")
        if not self.cookie_segura:
            problemas.append("COOKIE_SEGURA debe ser true (HTTPS)")
        if "*" in self.lista_cors or any(o.startswith("http://") for o in self.lista_cors):
            problemas.append("CORS_ORIGENES debe listar solo orígenes https explícitos")
        if problemas:
            raise RuntimeError("Configuración insegura para producción: " + "; ".join(problemas))

    cors_origenes: str = "http://localhost:5173"
    storage_dir: Path = RAIZ_PROYECTO / "storage"
    zona_horaria: str = "America/Guatemala"

    @property
    def mongodb_configurado(self) -> bool:
        uri = self.mongodb_uri.get_secret_value() if self.mongodb_uri else ""
        return uri.startswith(("mongodb://", "mongodb+srv://")) and "<" not in uri

    @property
    def lista_admin_correos(self) -> set[str]:
        return {c.strip().lower() for c in self.admin_correos.split(",") if c.strip()}

    @property
    def lista_cors(self) -> list[str]:
        return [o.strip() for o in self.cors_origenes.split(",") if o.strip()]


@lru_cache
def obtener_settings() -> Settings:
    return Settings()
