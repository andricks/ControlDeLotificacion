"""Conversión de montos a letras en español (formato de recibos y contratos)."""

from decimal import ROUND_HALF_UP, Decimal

_UNIDADES = ["", "UNO", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"]
_DIEZ_A_VEINTINUEVE = [
    "DIEZ",
    "ONCE",
    "DOCE",
    "TRECE",
    "CATORCE",
    "QUINCE",
    "DIECISÉIS",
    "DIECISIETE",
    "DIECIOCHO",
    "DIECINUEVE",
    "VEINTE",
    "VEINTIUNO",
    "VEINTIDÓS",
    "VEINTITRÉS",
    "VEINTICUATRO",
    "VEINTICINCO",
    "VEINTISÉIS",
    "VEINTISIETE",
    "VEINTIOCHO",
    "VEINTINUEVE",
]
_DECENAS = [
    "",
    "",
    "",
    "TREINTA",
    "CUARENTA",
    "CINCUENTA",
    "SESENTA",
    "SETENTA",
    "OCHENTA",
    "NOVENTA",
]
_CENTENAS = [
    "",
    "CIENTO",
    "DOSCIENTOS",
    "TRESCIENTOS",
    "CUATROCIENTOS",
    "QUINIENTOS",
    "SEISCIENTOS",
    "SETECIENTOS",
    "OCHOCIENTOS",
    "NOVECIENTOS",
]


def _menor_mil(n: int) -> str:
    centenas, resto = divmod(n, 100)
    partes = []
    if centenas:
        partes.append("CIEN" if n == 100 else _CENTENAS[centenas])
    if resto:
        if resto < 10:
            partes.append(_UNIDADES[resto])
        elif resto < 30:
            partes.append(_DIEZ_A_VEINTINUEVE[resto - 10])
        else:
            decena, unidad = divmod(resto, 10)
            partes.append(_DECENAS[decena] + (f" Y {_UNIDADES[unidad]}" if unidad else ""))
    return " ".join(partes)


def _apocopar(texto: str) -> str:
    """'UNO' → 'UN' delante de un sustantivo (MIL, MILLONES, QUETZALES)."""
    if texto.endswith("VEINTIUNO"):
        return texto[: -len("VEINTIUNO")] + "VEINTIÚN"
    if texto.endswith("UNO"):
        return texto[:-3] + "UN"
    return texto


def entero_a_letras(n: int) -> str:
    if n < 0 or n >= 1_000_000_000:
        raise ValueError("Monto fuera de rango para convertir a letras")
    if n == 0:
        return "CERO"
    millones, resto = divmod(n, 1_000_000)
    miles, unidades = divmod(resto, 1000)
    partes = []
    if millones:
        partes.append(
            "UN MILLÓN" if millones == 1 else f"{_apocopar(_menor_mil(millones))} MILLONES"
        )
    if miles:
        partes.append("MIL" if miles == 1 else f"{_apocopar(_menor_mil(miles))} MIL")
    if unidades:
        partes.append(_menor_mil(unidades))
    return " ".join(partes)


def monto_a_letras(
    monto: Decimal, moneda_singular: str = "QUETZAL", moneda_plural: str = "QUETZALES"
) -> str:
    """Decimal('10219.00') → 'DIEZ MIL DOSCIENTOS DIECINUEVE QUETZALES'.

    Con centavos: 'CIEN QUETZALES CON 50/100'.
    """
    monto = Decimal(monto).quantize(Decimal("0.01"), ROUND_HALF_UP)
    if monto < 0:
        raise ValueError("El monto no puede ser negativo")
    enteros = int(monto)
    centavos = int((monto - enteros) * 100)
    texto = _apocopar(entero_a_letras(enteros))
    if enteros % 1_000_000 == 0 and enteros:
        texto += " DE"  # "UN MILLÓN DE QUETZALES"
    resultado = f"{texto} {moneda_singular if enteros == 1 else moneda_plural}"
    if centavos:
        resultado += f" CON {centavos:02d}/100"
    return resultado
