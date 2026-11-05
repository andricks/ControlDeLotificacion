"""PDF del Estado de Cuenta de una Promesa de Compra Venta."""

import io
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core import formato as f
from app.modules.configuracion.models import ConfiguracionDatos
from app.modules.contratos.schemas import ContratoLeer
from app.modules.lotes.schemas import nombre_lotificacion
from app.modules.recibos.schemas import ReciboLeer
from app.pdf import estilos as e

ANCHO = LETTER[0] - 2 * e.MARGEN
ESTADOS_CUOTA = {"pagada": "Pagada", "parcial": "Parcial", "pendiente": "Pendiente"}
CONCEPTOS = {
    "enganche": "Enganche",
    "cuota": "Cuota",
    "abono_capital": "Abono capital",
    "otros": "Otros",
}


def _p(texto: object, estilo=e.base) -> Paragraph:
    return Paragraph(escape("" if texto is None else str(texto)), estilo)


def _grilla(filas: list[list], anchos: list[float], numeros_desde: int) -> Table:
    t = Table(filas, colWidths=[ANCHO * a for a in anchos], repeatRows=1)
    t.setStyle(e.TABLA_GRILLA)
    t.setStyle(TableStyle([("ALIGN", (numeros_desde, 1), (-1, -1), "RIGHT")]))
    return t


def construir_estado_cuenta(
    contrato: ContratoLeer, recibos: list[ReciboLeer], config: ConfiguracionDatos, al: datetime
) -> bytes:
    cond = contrato.condiciones
    hoy = al.date()
    pagadas = sum(1 for q in contrato.plan_cuotas if q.estado == "pagada")
    vencidas = sum(
        1
        for q in contrato.plan_cuotas
        if q.estado != "pagada" and (hoy - q.vencimiento).days > config.reglas.dias_gracia
    )

    resumen = [
        [
            "Total del inmueble",
            f.moneda(cond.total),
            "Cuota nivelada",
            f.moneda(cond.cuota_nivelada),
        ],
        [
            "Enganche pactado",
            f.moneda(cond.enganche),
            "Enganche pagado",
            f.moneda(contrato.total_pagado_enganche),
        ],
        [
            "Saldo financiado",
            f.moneda(cond.saldo_a_pagar),
            "Capital pagado",
            f.moneda(contrato.total_pagado_capital),
        ],
        [
            "Cuotas pagadas",
            f"{pagadas} de {len(contrato.plan_cuotas)}",
            "SALDO ACTUAL",
            f.moneda(contrato.saldo_capital),
        ],
        ["Cuotas vencidas", str(vencidas), "Estado", contrato.estado.replace("_", " ").upper()],
    ]
    tabla_resumen = Table(resumen, colWidths=[ANCHO * 0.22, ANCHO * 0.28] * 2)
    tabla_resumen.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTNAME", (3, 3), (3, 3), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.3, e.GRIS),
                ("BACKGROUND", (0, 0), (0, -1), e.GRIS_CLARO),
                ("BACKGROUND", (2, 0), (2, -1), e.GRIS_CLARO),
            ]
        )
    )

    filas_recibos = [
        [
            "No.",
            "Fecha",
            "Concepto",
            "Cuota",
            "Capital",
            "Interés",
            "Mora",
            "Abono",
            "Total",
            "Saldo",
        ]
    ]
    for r in recibos:
        d = r.desglose
        filas_recibos.append(
            [
                r.numero_formateado + (" (ANULADO)" if r.anulado else ""),
                f.fecha_corta(r.fecha),
                CONCEPTOS[r.concepto],
                r.cuota_numero or "",
                f.numero(d.capital),
                f.numero(d.intereses),
                f.numero(d.recargo_mora),
                f.numero(d.abono_capital),
                f.numero(r.total),
                f.numero(r.saldo_actual),
            ]
        )
    if len(filas_recibos) == 1:
        filas_recibos.append(["Sin recibos registrados"] + [""] * 9)

    filas_plan = [["No.", "Vencimiento", "Cuota", "Capital", "Interés", "Pagado", "Estado"]]
    for q in contrato.plan_cuotas:
        filas_plan.append(
            [
                q.numero,
                f.fecha_corta(q.vencimiento),
                f.numero(q.cuota),
                f.numero(q.capital),
                f.numero(q.interes),
                f.numero(q.capital_pagado + q.interes_pagado),
                ESTADOS_CUOTA[q.estado],
            ]
        )

    historia = [
        Paragraph(
            escape(nombre_lotificacion(contrato.lotificacion, config.proyecto)),
            e.encabezado_empresa,
        ),
        _p(config.empresa, e.negrita),
        Spacer(1, 3 * mm),
        Paragraph(
            f"ESTADO DE CUENTA · PROMESA Nº {contrato.numero_formateado}", e.titulo_documento
        ),
        Spacer(1, 2 * mm),
        _p(
            f"Cliente: {contrato.comprador.nombres_apellidos} · DPI {contrato.comprador.dpi} · "
            f"Lote {contrato.lote.codigo} · Fecha de corte: {f.fecha_corta(hoy)}",
            e.centro,
        ),
        Spacer(1, 3 * mm),
        tabla_resumen,
        Spacer(1, 4 * mm),
        _p("RECIBOS DE CAJA", e.negrita),
        _grilla(filas_recibos, [0.13, 0.09, 0.1, 0.06, 0.1, 0.1, 0.09, 0.1, 0.11, 0.12], 4),
        Spacer(1, 4 * mm),
        _p("PLAN DE CUOTAS", e.negrita),
        _grilla(filas_plan, [0.07, 0.15, 0.15, 0.15, 0.15, 0.15, 0.18], 2),
    ]
    if contrato.saldo_inicial:
        si = contrato.saldo_inicial
        historia.insert(
            7,
            _p(
                f"Saldo inicial cargado al {f.fecha_corta(si.fecha_corte)}: "
                f"{f.moneda(si.saldo_capital)} ({si.cuotas_pagadas} cuotas pagadas en papel).",
                e.pequeno,
            ),
        )

    buffer = io.BytesIO()
    generado = datetime.now(UTC).strftime("%d/%m/%Y %H:%M UTC")

    def pie(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(e.GRIS)
        canvas.drawString(
            e.MARGEN, 7 * mm, f"Estado de cuenta · Promesa Nº {contrato.numero_formateado}"
        )
        canvas.drawRightString(
            LETTER[0] - e.MARGEN, 7 * mm, f"Página {doc.page} · generado {generado}"
        )
        canvas.restoreState()

    SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=e.MARGEN,
        rightMargin=e.MARGEN,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
        title=f"Estado de cuenta {contrato.numero_formateado}",
        author=config.empresa,
        creator="Sistema Documental",
    ).build(historia, onFirstPage=pie, onLaterPages=pie)
    return buffer.getvalue()
