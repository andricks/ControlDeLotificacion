"""PDF del Reporte de Cobros y Morosidad (lista para cobranza)."""

import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core import formato as f
from app.core.tipos import CERO, GUATEMALA
from app.modules.cartera.schemas import CarteraLeer, SituacionPago
from app.modules.configuracion.models import ConfiguracionDatos
from app.modules.lotes.schemas import LOTIFICACIONES
from app.pdf import estilos as e

PAGINA = landscape(LETTER)
ANCHO = PAGINA[0] - 2 * e.MARGEN
LEYENDA = "Documento de control interno — no válido como factura fiscal"
TITULOS: dict[SituacionPago | None, str] = {
    "moroso": "CLIENTES MOROSOS",
    "en_gracia": "CLIENTES EN PERÍODO DE GRACIA",
    "por_vencer": "CLIENTES QUE PAGAN ESTA SEMANA",
    "al_dia": "CLIENTES AL DÍA",
    None: "TODOS LOS CLIENTES",
}
SITUACIONES = {
    "moroso": "Moroso",
    "en_gracia": "En gracia",
    "por_vencer": "Por vencer",
    "al_dia": "Al día",
}
ROJO_SUAVE = colors.HexColor("#fde8e8")


def _p(texto: object, estilo=e.base) -> Paragraph:
    return Paragraph(escape("" if texto is None else str(texto)), estilo)


def _lotificacion(clave: str) -> str:
    """'LOTIFICACIÓN "MONACO"' → 'Monaco' (la tabla no tiene espacio para el nombre largo)."""
    return LOTIFICACIONES[clave].removeprefix("LOTIFICACIÓN ").strip('"').title()


def construir_reporte_cartera(
    cartera: CarteraLeer,
    situacion: SituacionPago | None,
    lotificacion: str | None,
    config: ConfiguracionDatos,
) -> bytes:
    r = cartera.resumen
    titulo = f"REPORTE DE COBROS · {TITULOS[situacion]}"
    filtros = f"Fecha de corte: {f.fecha_corta(cartera.fecha)}"
    if lotificacion:
        filtros += f" · Lotificación: {_lotificacion(lotificacion)}"
    mora_pct = config.reglas.mora_pct_mensual.normalize()
    filtros += f" · {cartera.dias_gracia} días de gracia · Mora {mora_pct:f} % mensual"

    tabla_resumen = Table(
        [
            [
                "Clientes vigentes",
                "Morosos",
                "En gracia",
                "Pagan esta semana",
                "Al día",
                "Riesgo de rescisión",
                "Monto vencido",
                "Mora estimada",
            ],
            [
                r.clientes,
                r.morosos,
                r.en_gracia,
                r.por_vencer,
                r.al_dia,
                r.riesgo_rescision,
                f.moneda(r.monto_vencido),
                f.moneda(r.mora_estimada),
            ],
        ],
        colWidths=[ANCHO / 8] * 8,
    )
    tabla_resumen.setStyle(e.TABLA_GRILLA)
    tabla_resumen.setStyle(
        TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTSIZE", (0, 1), (-1, 1), 9)])
    )

    filas: list[list] = [
        ["No.", "Cliente / promesa", "Teléfono", "Lote", "Paga", "Próxima cuota", "Ctas. venc.",
         "Atraso", "Vencido", "Mora est.", "Total a cobrar", "Último pago"],
    ]  # fmt: skip
    riesgo: list[int] = []
    total_vencido = total_mora = CERO
    for i, c in enumerate(cartera.items, start=1):
        total_vencido += c.monto_vencido
        total_mora += c.mora_estimada
        if c.riesgo_rescision:
            riesgo.append(i)
        proxima = "Sin cuotas pendientes"
        if c.proxima_cuota_numero:
            vence = f.fecha_corta(c.proxima_vencimiento)
            proxima = f"No. {c.proxima_cuota_numero} de {c.numero_cuotas} · {vence}"
        atraso = (
            f"{c.dias_atraso} días"
            if c.situacion in ("moroso", "en_gracia")
            else SITUACIONES[c.situacion]
        )
        filas.append(
            [
                i,
                [_p(c.cliente_nombre, e.negrita), _p(f"Promesa {c.numero_formateado}", e.pequeno)],
                c.telefono or "",
                [_p(c.lote_codigo), _p(_lotificacion(c.lotificacion), e.pequeno)]
                if c.lotificacion
                else _p(c.lote_codigo),
                [_p(f"Día {c.dia_pago_mensual}"), _p(f.moneda(c.cuota_nivelada), e.pequeno)],
                _p(proxima),
                c.cuotas_vencidas or "",
                atraso,
                f.numero(c.monto_vencido) if c.monto_vencido else "",
                f.numero(c.mora_estimada) if c.mora_estimada else "",
                f.numero(c.monto_vencido + c.mora_estimada) if c.monto_vencido else "",
                f.fecha_corta(c.ultimo_pago) or "Ninguno",
            ]
        )
    vacio = len(filas) == 1
    if vacio:
        filas.append([_p("No hay clientes en esta situación.", e.centro)] + [""] * 11)
    filas.append(
        ["", _p("TOTAL", e.negrita)] + [""] * 6
        + [f.numero(total_vencido), f.numero(total_mora),
           f.numero(total_vencido + total_mora), ""]
    )  # fmt: skip

    anchos = [0.03, 0.17, 0.07, 0.08, 0.07, 0.14, 0.05, 0.07, 0.08, 0.07, 0.09, 0.08]
    tabla = Table(filas, colWidths=[ANCHO * a for a in anchos], repeatRows=1)
    tabla.setStyle(e.TABLA_GRILLA)
    estilo = [
        ("ALIGN", (6, 1), (6, -1), "CENTER"),
        ("ALIGN", (8, 1), (10, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), e.GRIS_CLARO),
    ]
    estilo += [("BACKGROUND", (0, fila), (-1, fila), ROJO_SUAVE) for fila in riesgo]
    if vacio:
        estilo.append(("SPAN", (0, 1), (-1, 1)))
    tabla.setStyle(TableStyle(estilo))

    historia = [
        _p(config.empresa, e.encabezado_empresa),
        Spacer(1, 2 * mm),
        Paragraph(escape(titulo), e.titulo_documento),
        Spacer(1, 1.5 * mm),
        _p(filtros, e.centro),
        Spacer(1, 3 * mm),
        tabla_resumen,
        Spacer(1, 4 * mm),
        tabla,
        Spacer(1, 2 * mm),
        _p(
            "Filas sombreadas: 2 o más cuotas en mora (la promesa puede rescindirse). "
            "La mora es estimada al día de corte; el monto definitivo se calcula al registrar "
            "el pago.",
            e.pequeno,
        ),
    ]

    buffer = io.BytesIO()
    generado = datetime.now(GUATEMALA).strftime("%d/%m/%Y %H:%M")

    def pie(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(e.GRIS)
        canvas.drawString(e.MARGEN, 7 * mm, f"Reporte de cobros · {LEYENDA}")
        canvas.drawRightString(
            PAGINA[0] - e.MARGEN, 7 * mm, f"Página {doc.page} · generado {generado}"
        )
        canvas.restoreState()

    SimpleDocTemplate(
        buffer,
        pagesize=PAGINA,
        leftMargin=e.MARGEN,
        rightMargin=e.MARGEN,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
        title=f"Reporte de cobros {f.fecha_corta(cartera.fecha)}",
        author=config.empresa,
        creator="Sistema Documental",
    ).build(historia, onFirstPage=pie, onLaterPages=pie)
    return buffer.getvalue()
