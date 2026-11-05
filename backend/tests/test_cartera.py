"""Cartera de cobro: situación de pago (pura) e integración con la base de pruebas."""

import io
from datetime import date
from decimal import Decimal as D

import pytest
from pypdf import PdfReader

from app.modules.auditoria.models import Auditoria
from app.modules.cartera.schemas import CarteraLeer
from app.modules.cartera.service import evaluar
from app.modules.configuracion.models import ConfiguracionDatos, ReglasNegocio
from app.modules.contratos.calculos import generar_plan
from app.modules.contratos.service import a_cuota_plan
from app.pdf.cartera import construir_reporte_cartera
from tests.datos import contrato_ejemplo

REGLAS = ReglasNegocio()  # 5 días de gracia, 5 % mensual
# Contrato real: 11 cuotas de 10,219 cada 30 desde el 28/02/2025.
PLAN = [a_cuota_plan(c) for c in generar_plan(D("112400"), 11, D("0"), date(2025, 2, 28), 30)]


@pytest.mark.parametrize(
    ("hoy", "situacion", "vencidas", "dias", "monto", "mora"),
    [
        (date(2025, 1, 23), "al_dia", 0, 0, "0.00", "0.00"),
        (date(2025, 2, 21), "por_vencer", 0, 0, "0.00", "0.00"),  # vence en 7 días
        (date(2025, 2, 28), "por_vencer", 0, 0, "0.00", "0.00"),  # vence hoy
        (date(2025, 3, 5), "en_gracia", 0, 5, "0.00", "0.00"),
        (date(2025, 3, 6), "moroso", 1, 6, "10219.00", "510.95"),
        # 46 días de la 1.ª (2 meses de mora) + 6 de la 2.ª (vence 30/03)
        (date(2025, 4, 14), "moroso", 2, 45, "20438.00", "1532.85"),
    ],
)
def test_evaluar(hoy, situacion, vencidas, dias, monto, mora):
    s = evaluar(PLAN, hoy, REGLAS)
    assert (s.situacion, s.cuotas_vencidas, s.dias_atraso) == (situacion, vencidas, dias)
    assert (s.monto_vencido, s.mora_estimada) == (D(monto), D(mora))
    assert s.proxima is not None and s.proxima.numero == 1


def test_evaluar_cuota_parcial_y_plan_terminado():
    plan = [q.model_copy() for q in PLAN]
    plan[0].capital_pagado, plan[0].estado = D("5000.00"), "parcial"
    s = evaluar(plan, date(2025, 3, 6), REGLAS)
    assert s.monto_vencido == D("5219.00")
    assert s.proxima is not None and s.proxima.numero == 1
    for q in plan:
        q.marcar_pagada()
    s = evaluar(plan, date(2030, 1, 1), REGLAS)
    assert (s.situacion, s.proxima, s.cuotas_vencidas) == ("al_dia", None, 0)


@pytest.mark.atlas
async def test_cartera_api(api):
    saldo_real = {"saldo_capital": "30648.00", "cuotas_pagadas": 8, "fecha_corte": "2025-10-01"}
    r = await api.post("/api/v1/contratos", json=contrato_ejemplo(saldo_inicial=saldo_real))
    moroso = r.json()
    r = await api.post(
        "/api/v1/contratos",
        json=contrato_ejemplo(
            lote__codigo="12-A01",
            comprador__dpi="2345678992101",
            comprador__nombres_apellidos="Ana Lucía Gómez Paz",
            condiciones__fecha_primera_cuota="2025-12-20",
            condiciones__dia_pago_mensual=20,
        ),
    )
    assert r.status_code == 201, r.text
    al_dia = r.json()
    r = await api.post(
        "/api/v1/recibos",
        json={"contrato_id": moroso["id"], "fecha": "2025-11-04", "concepto": "cuota",
              "cuota_numero": 9, "desglose": {"capital": "10219.00"}},
    )  # fmt: skip
    assert r.status_code == 201, r.text

    r = await api.get("/api/v1/cartera", params={"fecha": "2025-12-08"})
    assert r.status_code == 200, r.text
    datos = r.json()
    assert datos["dias_gracia"] == 5
    assert datos["resumen"] == {
        "clientes": 2, "morosos": 1, "en_gracia": 0, "por_vencer": 0, "al_dia": 1,
        "riesgo_rescision": 0, "monto_vencido": "10219.00", "mora_estimada": "510.95",
    }  # fmt: skip
    primero = datos["items"][0]
    assert primero["contrato_id"] == moroso["id"]
    assert (primero["situacion"], primero["proxima_cuota_numero"]) == ("moroso", 10)
    assert (primero["proxima_vencimiento"], primero["dias_atraso"]) == ("2025-11-30", 8)
    assert (primero["dia_pago_mensual"], primero["cuota_nivelada"]) == (30, "10219.00")
    assert (primero["cuotas_pagadas"], primero["numero_cuotas"]) == (9, 11)
    assert primero["ultimo_pago"] == "2025-11-04"
    assert primero["telefono"] == "5555-0000"
    assert datos["items"][1]["contrato_id"] == al_dia["id"]
    assert datos["items"][1]["ultimo_pago"] is None

    params = {"fecha": "2025-12-15", "situacion": "por_vencer"}
    solo = (await api.get("/api/v1/cartera", params=params)).json()
    assert [c["contrato_id"] for c in solo["items"]] == [al_dia["id"]]
    assert solo["total"] == 1 and solo["resumen"]["clientes"] == 2

    busqueda = (await api.get("/api/v1/cartera", params={"buscar": "gómez"})).json()
    assert [c["contrato_id"] for c in busqueda["items"]] == [al_dia["id"]]

    await api.post(f"/api/v1/contratos/{al_dia['id']}/eliminar", json={"motivo": "Prueba borrado"})
    assert (await api.get("/api/v1/cartera")).json()["resumen"]["clientes"] == 1


def _texto_pdf(contenido: bytes) -> str:
    assert contenido.startswith(b"%PDF-")
    return "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(contenido)).pages)


CARTERA = {
    "fecha": "2025-12-15", "dias_gracia": 5, "total": 1, "pagina": 1, "tamano": 1,
    "resumen": {"clientes": 3, "morosos": 1, "en_gracia": 0, "por_vencer": 1, "al_dia": 1,
                "riesgo_rescision": 1, "monto_vencido": "20438.00", "mora_estimada": "1532.85"},
    "items": [{
        "contrato_id": "c1", "numero_formateado": "00012",
        "cliente_nombre": "Juan Carlos Pérez Muñoz",
        "telefono": "5555-0000", "lotificacion": "monaco", "lote_codigo": "36-B34",
        "dia_pago_mensual": 30, "cuota_nivelada": "10219.00", "numero_cuotas": 11,
        "cuotas_pagadas": 8, "proxima_cuota_numero": 9, "proxima_vencimiento": "2025-10-30",
        "proxima_monto": "10219.00", "cuotas_vencidas": 2, "dias_atraso": 46,
        "monto_vencido": "20438.00", "mora_estimada": "1532.85", "enganche_pendiente": "0.00",
        "saldo_capital": "30648.00", "ultimo_pago": "2025-09-30", "situacion": "moroso",
        "riesgo_rescision": True,
    }],
}  # fmt: skip


def test_pdf_reporte_cobros():
    contenido = construir_reporte_cartera(
        CarteraLeer.model_validate(CARTERA), "moroso", "monaco", ConfiguracionDatos()
    )
    texto = _texto_pdf(contenido)
    for esperado in ["REPORTE DE COBROS · CLIENTES MOROSOS", "Fecha de corte: 15/12/2025",
                     "Lotificación: Monaco", "Juan Carlos Pérez Muñoz", "Promesa 00012",
                     "5555-0000", "36-B34", "Día 30", "No. 9 de 11 · 30/10/2025", "46 días",
                     "20,438.00", "1,532.85", "21,970.85", "30/09/2025", "TOTAL",
                     "no válido como factura fiscal"]:  # fmt: skip
        assert esperado in texto, esperado


def test_pdf_reporte_cobros_vacio():
    vacia = {**CARTERA, "items": [], "total": 0}
    texto = _texto_pdf(
        construir_reporte_cartera(
            CarteraLeer.model_validate(vacia), None, None, ConfiguracionDatos()
        )
    )
    assert "TODOS LOS CLIENTES" in texto
    assert "No hay clientes en esta situación." in texto


@pytest.mark.atlas
async def test_cartera_pdf_api(api):
    await api.post("/api/v1/contratos", json=contrato_ejemplo())
    r = await api.get("/api/v1/cartera/pdf", params={"situacion": "moroso", "fecha": "2025-03-10"})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf"
    assert 'filename="cobros_moroso_2025-03-10.pdf"' in r.headers["content-disposition"]
    texto = _texto_pdf(r.content)
    assert "Juan Carlos Pérez Muñoz" in texto and "10 días" in texto
    auditoria = await Auditoria.find_one(Auditoria.accion == "descargar_reporte_cobros")
    assert auditoria is not None and auditoria.detalle["clientes"] == 1


@pytest.mark.atlas
async def test_cartera_valida_parametros(api):
    r = await api.get("/api/v1/cartera", params={"situacion": "otra"})
    assert r.status_code == 422
    r = await api.get("/api/v1/cartera", params={"tamano": 500})
    assert r.status_code == 422


async def test_cartera_exige_sesion(cliente_http):
    assert (await cliente_http.get("/api/v1/cartera/pdf")).status_code == 401
