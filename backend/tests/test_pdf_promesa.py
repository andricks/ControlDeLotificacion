import io
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from pypdf import PdfReader

from app.modules.configuracion.models import ConfiguracionDatos
from app.modules.contratos.schemas import ContratoCrear, ContratoLeer
from app.modules.contratos.service import calcular
from app.pdf.promesa import construir_promesa
from tests.datos import DPI_COMPRADOR, contrato_ejemplo


def _contrato_leer(**cambios) -> ContratoLeer:
    c = ContratoCrear.model_validate(contrato_ejemplo(**cambios))
    calc = calcular(c.condiciones)
    return ContratoLeer(
        id="0" * 24,
        numero=184,
        numero_formateado="00184",
        fecha_firma=c.fecha_firma,
        lotificacion=c.lotificacion,
        cliente_id="1" * 24,
        lote_id="2" * 24,
        comprador=c.comprador,
        conyuge_gestor=c.conyuge_gestor,
        dependientes=c.dependientes,
        lote=c.lote,
        condiciones=calc.condiciones,
        plan_cuotas=calc.plan_cuotas,
        notario=c.notario,
        total_pagado_capital="0",
        saldo_capital=calc.condiciones.saldo_a_pagar,
        estado="vigente",
        creado_en=datetime.now(UTC),
    )


def _texto(pdf: bytes) -> list[str]:
    return [p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages]


def test_pdf_promesa_contiene_los_datos_clave():
    pdf = construir_promesa(_contrato_leer(), ConfiguracionDatos())
    assert pdf.startswith(b"%PDF-")
    paginas = _texto(pdf)
    assert len(paginas) == 3  # datos, condiciones generales, plan de pagos
    p1 = paginas[0]
    for esperado in [
        "00184",
        "Juan Carlos Pérez Muñoz",
        DPI_COMPRADOR,
        "36-B34",
        "Q 122,400.00",
        "Q 112,400.00",
        "Q 10,219.00",
        "11 CUOTAS",
        "28/02/2025",
        "EL DÍA 22 DE ENERO DE DOS MIL VEINTICINCO",
        "EDAD:",
        "48",  # edad del comprador a la fecha de firma
    ]:
        assert esperado in p1, esperado
    assert "CONDICIONES GENERALES" in paginas[1]
    assert "BORRADOR" in paginas[1]  # texto aún no validado
    assert "10,210.00" in paginas[2]  # última cuota ajustada en el anexo


def test_pdf_sin_borrador_cuando_condiciones_validadas():
    cfg = ConfiguracionDatos(condiciones_generales_validadas=True)
    paginas = _texto(construir_promesa(_contrato_leer(), cfg))
    assert "BORRADOR" not in paginas[1]


def test_pdf_usa_el_texto_de_textos_py(monkeypatch):
    monkeypatch.setattr(
        "app.pdf.promesa.CONDICIONES_GENERALES", [("CLAUSULA NUEVA", "Texto editado a mano.")]
    )
    paginas = _texto(construir_promesa(_contrato_leer(), ConfiguracionDatos()))
    assert "CLAUSULA NUEVA" in paginas[1]
    assert "Texto editado a mano." in paginas[1]


def test_pdf_muestra_proyecto_y_cuentas_bancarias():
    paginas = _texto(construir_promesa(_contrato_leer(), ConfiguracionDatos()))
    p1 = " ".join(paginas[0].split())
    assert "TABLON CAMPESTRE2" in p1
    assert "INMOBILIARIA ESTRADA" in p1
    assert "Kilómetro 124.5" in p1
    assert "5381-4009" in p1
    for esperado in ["BANRURAL", "4269194666", "BANCO INDUSTRIAL", "4516652"]:
        assert esperado in p1, esperado
    assert "ANDRICK SAUL ESTRADA AGUILAR" in p1


@pytest.mark.parametrize(
    ("lotificacion", "esperado", "ausente"),
    [
        ("monaco", 'LOTIFICACIÓN "MONACO"', "TABLON"),
        ("finca_el_ensueno", 'LOTIFICACIÓN "FINCA EL ENSUEÑO"', "TABLON"),
        ("tablon_campestre2", 'LOTIFICACIÓN "TABLON CAMPESTRE2"', "MONACO"),
    ],
)
def test_pdf_muestra_la_lotificacion_elegida(lotificacion, esperado, ausente):
    contrato = _contrato_leer(lotificacion=lotificacion)
    p1 = " ".join(_texto(construir_promesa(contrato, ConfiguracionDatos()))[0].split())
    assert p1.count(esperado) == 2  # encabezado y cláusula de arras
    assert ausente not in p1


@pytest.mark.parametrize(
    ("lotificacion", "drenaje"),
    [
        ("monaco", "2.Red de distribución de drenaje. 3.Red de Distribución de Energía"),
        ("finca_el_ensueno", "2.Drenajes unicamente se permite Fosas Sépticas. 3.Red"),
        ("tablon_campestre2", "2.Drenajes unicamente se permite Fosas Sépticas. 3.Red"),
    ],
)
def test_obras_de_urbanizacion_segun_lotificacion(lotificacion, drenaje):
    contrato = _contrato_leer(lotificacion=lotificacion)
    p2 = " ".join(_texto(construir_promesa(contrato, ConfiguracionDatos()))[1].split())
    assert drenaje in p2
    assert "1. Mojones señalando" in p2  # el resto de la cláusula no cambia
    assert "c) Avisar al promitente vendedor" in p2
    uso = "d) Hacer uso adecuado del sistema de {} de aguas negras."
    if lotificacion == "monaco":
        assert "Drenajes unicamente" not in p2
        assert uso.format("drenaje") in p2
        assert "fosas septicas" not in p2
    else:
        assert uso.format("fosas septicas") in p2


def test_pdf_promesa_antigua_sin_lotificacion_usa_configuracion():
    contrato = _contrato_leer().model_copy(update={"lotificacion": None})
    cfg = ConfiguracionDatos(proyecto="PROYECTO DE CONFIGURACIÓN")
    p1 = " ".join(_texto(construir_promesa(contrato, cfg))[0].split())
    assert "PROYECTO DE CONFIGURACIÓN" in p1


def test_lotificacion_es_obligatoria_y_solo_de_la_lista():
    datos = contrato_ejemplo()
    del datos["lotificacion"]
    with pytest.raises(ValidationError):
        ContratoCrear.model_validate(datos)
    with pytest.raises(ValidationError):
        ContratoCrear.model_validate(contrato_ejemplo(lotificacion="otra"))


def test_pdf_clausula_sin_texto_muestra_solo_titulo(monkeypatch):
    monkeypatch.setattr("app.pdf.promesa.CONDICIONES_GENERALES", [("SOLO TITULO", "")])
    paginas = _texto(construir_promesa(_contrato_leer(), ConfiguracionDatos()))
    assert "SOLO TITULO" in paginas[1]


def test_pdf_sin_conyuge_ni_saldo():
    contrato = _contrato_leer(
        conyuge_gestor=None,
        condiciones__enganche="122400.00",
        condiciones__enganche_fraccionado=[],
    )
    paginas = _texto(construir_promesa(contrato, ConfiguracionDatos()))
    assert len(paginas) == 2  # sin anexo de plan porque no hay saldo financiado
