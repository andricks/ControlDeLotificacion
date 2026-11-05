"""Validaciones de documentos de identificación guatemaltecos."""

import re


def normalizar_nit(nit: str) -> str:
    return re.sub(r"[\s-]", "", nit or "").upper()


def nit_valido(nit: str) -> bool:
    """NIT con dígito verificador módulo 11 (puede ser 'K'). 'CF' = Consumidor Final."""
    nit = normalizar_nit(nit)
    if nit == "CF":
        return True
    if len(nit) < 2 or not nit[:-1].isdigit():
        return False
    cuerpo, verificador = nit[:-1], nit[-1]
    suma = sum(int(d) * p for d, p in zip(cuerpo, range(len(cuerpo) + 1, 1, -1), strict=True))
    esperado = (11 - suma % 11) % 11
    return verificador == ("K" if esperado == 10 else str(esperado))


def normalizar_dpi(dpi: str) -> str:
    return re.sub(r"\s", "", dpi or "")


def dpi_valido(dpi: str) -> bool:
    """DPI/CUI: 13 dígitos = 8 correlativo + 1 verificador + 2 departamento + 2 municipio."""
    dpi = normalizar_dpi(dpi)
    if not re.fullmatch(r"\d{13}", dpi):
        return False
    correlativo, verificador = dpi[:8], int(dpi[8])
    departamento, municipio = int(dpi[9:11]), int(dpi[11:13])
    if not (1 <= departamento <= 22 and municipio >= 1):
        return False
    suma = sum(int(d) * (i + 2) for i, d in enumerate(correlativo))
    return suma % 11 == verificador
