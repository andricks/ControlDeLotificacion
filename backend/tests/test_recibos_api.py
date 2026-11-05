"""Integración de recibos contra la base de pruebas en Atlas (facturas_test)."""

import io

import pytest
from pypdf import PdfReader

from app.ajustar_correlativo import ajustar
from tests.datos import contrato_ejemplo

pytestmark = pytest.mark.atlas

SALDO_INICIAL_REAL = {"saldo_capital": "30648.00", "cuotas_pagadas": 8, "fecha_corte": "2025-10-01"}


async def _contrato(api, **cambios) -> dict:
    r = await api.post("/api/v1/contratos", json=contrato_ejemplo(**cambios))
    assert r.status_code == 201, r.text
    return r.json()


async def _recibo(api, contrato_id, concepto, desglose, fecha="2025-11-04", **extra):
    return await api.post(
        "/api/v1/recibos",
        json={"contrato_id": contrato_id, "fecha": fecha, "concepto": concepto,
              "desglose": desglose, **extra},
    )  # fmt: skip


async def test_cliente_del_papel_reproduce_recibo_real(api, bd):
    await ajustar(bd, "recibo", 2539)  # continuar la numeración del papel
    c = await _contrato(api, saldo_inicial=SALDO_INICIAL_REAL)
    assert c["saldo_capital"] == "30648.00"
    assert c["total_pagado_enganche"] == "10000.00"
    assert [q["estado"] for q in c["plan_cuotas"]].count("pagada") == 8

    s = (await api.get("/api/v1/recibos/sugerencia",
                       params={"contrato_id": c["id"], "fecha": "2025-11-04"})).json()  # fmt: skip
    assert (s["cuota_numero"], s["cuota_mes"]) == (9, "octubre, 2025")
    assert (s["capital"], s["recargo_mora"], s["dias_atraso"]) == ("10219.00", "0.00", 5)

    r = await _recibo(
        api, c["id"], "cuota", {"capital": "10219.00"}, cuota_numero=9, numero_fel="2540",
        boletas=[{"numero": "88507709", "cuenta": "110-018984-2"}],
    )  # fmt: skip
    assert r.status_code == 201, r.text
    rec = r.json()
    assert rec["numero"] == 2540
    assert (rec["saldo_anterior"], rec["saldo_actual"]) == ("30648.00", "20429.00")
    assert rec["total_en_letras"] == "DIEZ MIL DOSCIENTOS DIECINUEVE QUETZALES"
    assert rec["cuota_mes"] == "octubre, 2025"

    detalle = (await api.get(f"/api/v1/contratos/{c['id']}")).json()
    assert detalle["saldo_capital"] == "20429.00"
    assert detalle["plan_cuotas"][8]["estado"] == "pagada"

    pdf = await api.get(f"/api/v1/recibos/{rec['id']}/pdf")
    assert pdf.status_code == 200
    texto = PdfReader(io.BytesIO(pdf.content)).pages[0].extract_text()
    for esperado in ["RECIBO DE CAJA", "No. 002540", "FEL 2540", "Jalapa, 4 de noviembre del 2025",
                     "DIEZ MIL DOSCIENTOS DIECINUEVE QUETZALES", "Cuota Nivelada No. 9",
                     "octubre, 2025", "Q 30,648.00", "Q 20,429.00", "88507709 / 110-018984-2",
                     "ORIGINAL", "COPIA"]:  # fmt: skip
        assert esperado in texto, esperado


async def test_mora_sugerida_despues_de_gracia(api):
    c = await _contrato(api, saldo_inicial=SALDO_INICIAL_REAL)
    s = (await api.get("/api/v1/recibos/sugerencia",
                       params={"contrato_id": c["id"], "fecha": "2025-11-06"})).json()  # fmt: skip
    assert s["recargo_mora"] == "510.95"
    assert s["total_sugerido"] == "10729.95"


async def test_cuotas_en_orden_y_sin_exceder(api):
    c = await _contrato(api)
    r = await _recibo(api, c["id"], "cuota", {"capital": "10219"}, cuota_numero=2)
    assert r.status_code == 422 and "la siguiente pendiente es la No. 1" in r.text
    r = await _recibo(api, c["id"], "cuota", {"capital": "10220"}, cuota_numero=1)
    assert r.status_code == 422 and "abono a capital" in r.text
    # pago parcial y luego completar la misma cuota
    assert (
        await _recibo(api, c["id"], "cuota", {"capital": "5000"}, cuota_numero=1)
    ).status_code == 201
    plan = (await api.get(f"/api/v1/contratos/{c['id']}")).json()["plan_cuotas"]
    assert plan[0]["estado"] == "parcial"
    assert (
        await _recibo(api, c["id"], "cuota", {"capital": "5219"}, cuota_numero=1)
    ).status_code == 201
    detalle = (await api.get(f"/api/v1/contratos/{c['id']}")).json()
    assert detalle["plan_cuotas"][0]["estado"] == "pagada"
    assert detalle["saldo_capital"] == "102181.00"


async def test_abono_capital_reglas_y_reprogramacion(api):
    c = await _contrato(api, saldo_inicial=SALDO_INICIAL_REAL)
    # atrasado: la cuota 9 venció el 30/10 → no puede abonar el 04/11
    r = await _recibo(api, c["id"], "abono_capital", {"abono_capital": "5000"})
    assert r.status_code == 422 and "al día" in r.text
    # cuota + abono en el mismo recibo, al día
    r = await _recibo(
        api, c["id"], "cuota", {"capital": "10219", "abono_capital": "1000"}, cuota_numero=9,
        fecha="2025-10-30",
    )  # fmt: skip
    assert r.status_code == 422 and "menor de Q 2,000.00" in r.text
    r = await _recibo(
        api, c["id"], "cuota", {"capital": "10219", "abono_capital": "5000"}, cuota_numero=9,
        fecha="2025-10-30",
    )  # fmt: skip
    assert r.status_code == 201, r.text
    assert r.json()["saldo_actual"] == "15429.00"
    plan = (await api.get(f"/api/v1/contratos/{c['id']}")).json()["plan_cuotas"]
    pendientes = [q for q in plan if q["estado"] != "pagada"]
    assert [(q["numero"], q["cuota"]) for q in pendientes] == [(10, "10219.00"), (11, "5210.00")]


async def test_cancelar_todo_marca_contrato_y_lote(api, bd):
    c = await _contrato(api, saldo_inicial=SALDO_INICIAL_REAL)
    r = await _recibo(api, c["id"], "abono_capital", {"abono_capital": "30648.00"},
                      fecha="2025-10-01")  # fmt: skip
    assert r.status_code == 201, r.text
    detalle = (await api.get(f"/api/v1/contratos/{c['id']}")).json()
    assert detalle["estado"] == "cancelado_total"
    assert (await bd["lotes"].find_one({"codigo": "36-B34"}))["estado"] == "vendido"
    r = await _recibo(api, c["id"], "otros", {"otros": "10"})
    assert r.status_code == 422 and "no está vigente" in r.text


async def test_anular_solo_el_ultimo_y_revierte_todo(api):
    c = await _contrato(api, saldo_inicial=SALDO_INICIAL_REAL)
    r1 = (await _recibo(api, c["id"], "cuota", {"capital": "10219"}, cuota_numero=9)).json()
    r2 = (await _recibo(api, c["id"], "otros", {"otros": "50"}, observaciones="Constancia")).json()

    r = await api.post(f"/api/v1/recibos/{r1['id']}/anular", json={"motivo": "Error de digitación"})
    assert r.status_code == 409 and r.json()["codigo"] == "NO_ES_ULTIMO_RECIBO"

    assert (await api.post(f"/api/v1/recibos/{r2['id']}/anular",
                           json={"motivo": "Cobro duplicado"})).status_code == 200  # fmt: skip
    r = await api.post(f"/api/v1/recibos/{r1['id']}/anular", json={"motivo": "Error de digitación"})
    assert r.status_code == 200 and r.json()["anulado"] is True
    detalle = (await api.get(f"/api/v1/contratos/{c['id']}")).json()
    assert detalle["saldo_capital"] == "30648.00"
    assert detalle["plan_cuotas"][8]["estado"] == "pendiente"
    r = await api.post(f"/api/v1/recibos/{r1['id']}/anular", json={"motivo": "Otra vez"})
    assert r.status_code == 409

    pdf = await api.get(f"/api/v1/recibos/{r1['id']}/pdf")
    assert "RECIBO ANULADO" in PdfReader(io.BytesIO(pdf.content)).pages[0].extract_text()


async def test_borrar_recibo_revierte_y_lo_oculta(api, bd):
    c = await _contrato(api, saldo_inicial=SALDO_INICIAL_REAL)
    r1 = (await _recibo(api, c["id"], "cuota", {"capital": "10219"}, cuota_numero=9)).json()
    r2 = (await _recibo(api, c["id"], "otros", {"otros": "50"})).json()

    r = await api.post(f"/api/v1/recibos/{r1['id']}/eliminar", json={"motivo": "Prueba de borrado"})
    assert r.status_code == 409 and r.json()["codigo"] == "NO_ES_ULTIMO_RECIBO"
    r = await api.post(f"/api/v1/recibos/{r2['id']}/eliminar", json={"motivo": "x"})
    assert r.status_code == 422  # motivo muy corto

    for rec in (r2, r1):
        r = await api.post(f"/api/v1/recibos/{rec['id']}/eliminar",
                           json={"motivo": "Recibo de prueba"})  # fmt: skip
        assert r.status_code == 200, r.text
    detalle = (await api.get(f"/api/v1/contratos/{c['id']}")).json()
    assert detalle["saldo_capital"] == "30648.00"
    assert detalle["plan_cuotas"][8]["estado"] == "pendiente"

    lista = (await api.get("/api/v1/recibos", params={"contrato_id": c["id"]})).json()
    assert lista["total"] == 0
    assert (await api.get(f"/api/v1/recibos/{r1['id']}")).status_code == 404
    assert (await api.get(f"/api/v1/recibos/{r1['id']}/pdf")).status_code == 404
    # sigue en la base (borrado lógico) y queda en auditoría
    assert (await bd["recibos"].find_one({"numero": r1["numero"]}))["eliminado_en"] is not None
    assert await bd["auditoria"].count_documents({"accion": "eliminar"}) == 2


async def test_borrar_recibo_anulado_no_toca_saldos(api):
    c = await _contrato(api, saldo_inicial=SALDO_INICIAL_REAL)
    r1 = (await _recibo(api, c["id"], "cuota", {"capital": "10219"}, cuota_numero=9)).json()
    await api.post(f"/api/v1/recibos/{r1['id']}/anular", json={"motivo": "Error de digitación"})
    r2 = (await _recibo(api, c["id"], "cuota", {"capital": "10219"}, cuota_numero=9)).json()
    # el anulado se puede borrar aunque no sea el último
    r = await api.post(f"/api/v1/recibos/{r1['id']}/eliminar", json={"motivo": "Limpieza"})
    assert r.status_code == 200, r.text
    detalle = (await api.get(f"/api/v1/contratos/{c['id']}")).json()
    assert detalle["saldo_capital"] == r2["saldo_actual"] == "20429.00"


async def test_borrar_promesa_borra_recibos_y_libera_lote(api, bd):
    c = await _contrato(api, saldo_inicial=SALDO_INICIAL_REAL)
    await _recibo(api, c["id"], "cuota", {"capital": "10219"}, cuota_numero=9)

    r = await api.post(
        f"/api/v1/contratos/{c['id']}/eliminar", json={"motivo": "Promesa de prueba"}
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"id": c["id"], "numero_formateado": c["numero_formateado"],
                        "recibos_eliminados": 1}  # fmt: skip

    assert (await api.get(f"/api/v1/contratos/{c['id']}")).status_code == 404
    assert (await api.get(f"/api/v1/contratos/{c['id']}/pdf")).status_code == 404
    assert (await api.get("/api/v1/contratos")).json()["total"] == 0
    assert (await api.get("/api/v1/recibos")).json()["total"] == 0
    r = await _recibo(api, c["id"], "otros", {"otros": "10"})
    assert r.status_code == 404
    r = await api.post(f"/api/v1/contratos/{c['id']}/eliminar", json={"motivo": "Otra vez"})
    assert r.status_code == 404

    lote = await bd["lotes"].find_one({"codigo": "36-B34"})
    assert (lote["estado"], lote["contrato_id"]) == ("disponible", None)
    # el lote liberado se puede volver a vender en una promesa nueva
    nueva = await _contrato(api)
    assert nueva["numero"] == c["numero"] + 1


async def test_enganche_no_excede_lo_pactado(api):
    c = await _contrato(api)
    s = (await api.get("/api/v1/recibos/sugerencia", params={"contrato_id": c["id"]})).json()
    assert s["enganche_pendiente"] == "10000.00"
    assert (await _recibo(api, c["id"], "enganche", {"enganche": "10000"},
                          fecha="2025-01-22")).status_code == 201  # fmt: skip
    r = await _recibo(api, c["id"], "enganche", {"enganche": "1"}, fecha="2025-01-22")
    assert r.status_code == 422 and "enganche pendiente es Q 0.00" in r.text


async def test_estado_de_cuenta_pdf_y_listado(api):
    c = await _contrato(api, saldo_inicial=SALDO_INICIAL_REAL)
    await _recibo(api, c["id"], "cuota", {"capital": "10219"}, cuota_numero=9)
    lista = (await api.get("/api/v1/recibos", params={"contrato_id": c["id"]})).json()
    assert lista["total"] == 1
    assert (await api.get("/api/v1/recibos", params={"buscar": "pérez"})).json()["total"] == 1

    r = await api.get(f"/api/v1/contratos/{c['id']}/estado-cuenta/pdf")
    assert r.status_code == 200
    texto = PdfReader(io.BytesIO(r.content)).pages[0].extract_text()
    for esperado in ["ESTADO DE CUENTA", "Q 20,429.00", "9 de 11", "Saldo inicial cargado"]:
        assert esperado in texto, esperado


async def test_saldo_inicial_invalido(api):
    r = await api.post(
        "/api/v1/contratos",
        json=contrato_ejemplo(saldo_inicial={**SALDO_INICIAL_REAL, "saldo_capital": "999999"}),
    )
    assert r.status_code == 422 and "no puede ser mayor" in r.text
