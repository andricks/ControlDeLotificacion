"""Pruebas de integración contra la base de pruebas en Atlas (facturas_test)."""

import pytest

from tests.datos import DPI_COMPRADOR, contrato_ejemplo

pytestmark = pytest.mark.atlas


async def test_crear_promesa_guarda_todo_y_numera(api):
    r = await api.post("/api/v1/contratos", json=contrato_ejemplo())
    assert r.status_code == 201, r.text
    c = r.json()
    assert c["numero"] == 1
    assert c["numero_formateado"] == "00001"
    assert c["condiciones"]["total"] == "122400.00"
    assert c["saldo_capital"] == "112400.00"
    assert len(c["plan_cuotas"]) == 11
    assert c["estado"] == "vigente"

    # el cliente queda guardado y se puede buscar por DPI (autocompletar)
    cli = await api.get(f"/api/v1/clientes/por-dpi/{DPI_COMPRADOR}")
    assert cli.status_code == 200
    assert cli.json()["nombres_apellidos"] == "Juan Carlos Pérez Muñoz"

    # detalle y listado
    assert (await api.get(f"/api/v1/contratos/{c['id']}")).json()["lote"]["codigo"] == "36-B34"
    lista = (await api.get("/api/v1/contratos", params={"buscar": "pérez"})).json()
    assert lista["total"] == 1
    assert lista["items"][0]["lote_codigo"] == "36-B34"


async def test_correlativo_avanza_y_cliente_se_actualiza(api):
    await api.post("/api/v1/contratos", json=contrato_ejemplo())
    r = await api.post(
        "/api/v1/contratos",
        json=contrato_ejemplo(lote__codigo="36-B35", comprador__telefono="4444-1111"),
    )
    assert r.status_code == 201
    assert r.json()["numero"] == 2
    cli = (await api.get(f"/api/v1/clientes/por-dpi/{DPI_COMPRADOR}")).json()
    assert cli["telefono"] == "4444-1111"  # mismo DPI → se actualiza, no se duplica
    assert (await api.get("/api/v1/clientes")).json()["total"] == 1


async def test_lote_ya_reservado_da_conflicto_y_no_consume_numero(api):
    assert (await api.post("/api/v1/contratos", json=contrato_ejemplo())).status_code == 201
    r = await api.post("/api/v1/contratos", json=contrato_ejemplo())
    assert r.status_code == 409
    assert r.json()["codigo"] == "LOTE_NO_DISPONIBLE"
    # la transacción revirtió el correlativo: el siguiente contrato es el 2
    r = await api.post("/api/v1/contratos", json=contrato_ejemplo(lote__codigo="99-A01"))
    assert r.json()["numero"] == 2


async def test_mismo_lote_en_otra_lotificacion_si_se_puede_vender(api):
    assert (await api.post("/api/v1/contratos", json=contrato_ejemplo())).status_code == 201
    r = await api.post("/api/v1/contratos", json=contrato_ejemplo(lotificacion="monaco"))
    assert r.status_code == 201, r.text
    c = r.json()
    assert c["lotificacion"] == "monaco"
    lista = (await api.get("/api/v1/contratos")).json()
    assert sorted(i["lotificacion"] for i in lista["items"]) == ["monaco", "tablon_campestre2"]
    pdf = await api.get(f"/api/v1/contratos/{c['id']}/pdf")
    assert pdf.status_code == 200


async def test_sin_lotificacion_422(api):
    datos = contrato_ejemplo()
    del datos["lotificacion"]
    r = await api.post("/api/v1/contratos", json=datos)
    assert r.status_code == 422


async def test_descargar_pdf_y_auditoria(api, bd):
    c = (await api.post("/api/v1/contratos", json=contrato_ejemplo())).json()
    r = await api.get(f"/api/v1/contratos/{c['id']}/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF-")
    assert 'filename="promesa_00001_lote_36-B34.pdf"' in r.headers["content-disposition"]
    acciones = [d["accion"] async for d in bd["auditoria"].find({}, {"accion": 1})]
    assert sorted(acciones) == ["crear", "descargar_pdf"]


async def test_datos_invalidos_422_con_mensaje(api):
    r = await api.post("/api/v1/contratos", json=contrato_ejemplo(comprador__dpi="123"))
    assert r.status_code == 422
    assert "DPI inválido" in r.text


async def test_ids_inexistentes_o_mal_formados_404(api):
    assert (await api.get("/api/v1/contratos/no-es-un-id")).status_code == 404
    assert (await api.get("/api/v1/contratos/" + "a" * 24)).status_code == 404
    assert (await api.get("/api/v1/contratos/" + "a" * 24 + "/pdf")).status_code == 404
    assert (await api.get("/api/v1/clientes/por-dpi/1234567892101")).status_code == 404


async def test_busqueda_no_permite_inyeccion_de_operadores(api):
    await api.post("/api/v1/contratos", json=contrato_ejemplo())
    r = await api.get("/api/v1/contratos", params={"buscar": '{"$ne": null}'})
    assert r.status_code == 200
    assert r.json()["total"] == 0
    r = await api.get("/api/v1/contratos", params={"buscar": ".*"})
    assert r.json()["total"] == 0  # el texto se escapa, no es regex


async def test_calcular_vista_previa_no_guarda(api, bd):
    r = await api.post(
        "/api/v1/contratos/calcular", json={"condiciones": contrato_ejemplo()["condiciones"]}
    )
    assert r.status_code == 200
    assert r.json()["condiciones"]["cuota_nivelada"] == "10219.00"
    assert await bd["contratos"].count_documents({}) == 0
