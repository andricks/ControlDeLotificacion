"""PDF del Recibo de Caja: ORIGINAL (cliente) y COPIA (caja) en una hoja carta."""

import io
from decimal import Decimal
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core import formato as f
from app.modules.configuracion.models import ConfiguracionDatos
from app.modules.lotes.schemas import nombre_lotificacion
from app.modules.recibos.schemas import ReciboLeer
from app.pdf import estilos as e

ANCHO = LETTER[0] - 2 * e.MARGEN
INTERIOR = ANCHO - 12  # descuenta el relleno de la celda que contiene el encabezado
ROJO = colors.HexColor("#b91c1c")
NUMERO = ParagraphStyle("numero_recibo", parent=e.centro, fontSize=13, leading=16, textColor=ROJO)
FEL = ParagraphStyle("fel", parent=e.centro, fontSize=9, leading=11, textColor=ROJO)


def _p(texto: object, estilo=e.base) -> Paragraph:
    return Paragraph(escape("" if texto is None else str(texto)), estilo)


def _campo(etiqueta: str, valor: object) -> Paragraph:
    return Paragraph(f"<b>{escape(etiqueta)}</b> {escape(str(valor))}", e.base)


def _fecha_larga(r: ReciboLeer) -> str:
    return f"{r.lugar}, {r.fecha.day} de {f.mes_nombre(r.fecha).lower()} del {r.fecha.year}"


def _q(valor: Decimal) -> str:
    return f.moneda(valor, "Q")


def _bloque(r: ReciboLeer, cfg: ConfiguracionDatos, copia: str) -> Table:
    d = r.desglose
    derecha = [
        Paragraph("RECIBO DE CAJA", e.titulo_documento),
        Paragraph(f"No. {r.numero_formateado}", NUMERO),
    ]
    if r.numero_fel:
        derecha.append(Paragraph(f"FEL {escape(r.numero_fel)}", FEL))
    derecha.append(_p(copia, e.centro_pequeno))
    encabezado = Table(
        [
            [
                [
                    Paragraph(
                        escape(nombre_lotificacion(r.lotificacion, cfg.proyecto)),
                        e.encabezado_empresa,
                    ),
                    _p(cfg.empresa, e.negrita),
                    _p(
                        f"OFICINAS: {cfg.direccion_oficinas} — Tel. {cfg.telefono_oficinas}",
                        e.pequeno,
                    ),
                    _p(f"Ubicado en: {cfg.direccion_proyecto}", e.pequeno),
                ],
                derecha,
            ]
        ],
        colWidths=[INTERIOR * 0.66, INTERIOR * 0.34],  # cabe dentro del marco del recibo
    )
    encabezado.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))

    concepto: list[list] = []
    if d.enganche:
        concepto.append([_campo("ENGANCHE:", _q(d.enganche)), ""])
    if r.concepto == "cuota":
        concepto.append(
            [
                Paragraph(
                    f"<b><i>Cuota Nivelada No. {r.cuota_numero}</i> Correspondiente al mes de:</b> "
                    f"{escape(r.cuota_mes or '')}",
                    e.base,
                ),
                "",
            ]
        )
        concepto.append([_campo("Capital:", _q(d.capital)), _campo("Intereses:", _q(d.intereses))])
    concepto.append(
        [
            _campo("(+) Recargo por mora:", _q(d.recargo_mora)),
            _campo("(+) Abono Capital:", _q(d.abono_capital)),
        ]
    )
    concepto.append([_campo("(+) Otros:", _q(d.otros)), ""])
    tabla_concepto = Table(concepto, colWidths=[ANCHO * 0.45, ANCHO * 0.35])
    tabla_concepto.setStyle(
        TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)])
    )

    boletas = [_p(f"{b.numero} / {b.cuenta}" if b.cuenta else b.numero) for b in r.boletas] or [
        _p("—")
    ]
    saldo = Table(
        [
            [
                [
                    _campo("Saldo anterior:", _q(r.saldo_anterior)),
                    _campo("(-) Este pago:", _q(d.reduce_saldo)),
                    _campo("Saldo actual:", _q(r.saldo_actual)),
                ],
                [_p("BOLETAS RELACIONADAS (número / cuenta):", e.negrita), *boletas],
            ]
        ],
        colWidths=[ANCHO * 0.45, ANCHO * 0.55],
    )
    saldo.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))

    filas = [
        [encabezado, ""],
        [Paragraph(escape(_fecha_larga(r)), e.base), ""],
        [_campo("Recibimos de:", r.cliente_nombre), _p(_q(r.total), e.negrita)],
        [_campo("La cantidad de:", r.total_en_letras), ""],
        [
            _campo(
                "Correspondiente a los lotes No.:",
                f"{r.lotes_texto}  ·  Promesa No. {r.contrato_numero:05d}",
            ),
            "",
        ],
        [_p("EN CONCEPTO DE", e.negrita), _p("TOTAL", e.negrita)],
        [tabla_concepto, _p(_q(r.total), e.negrita)],
        [_p("SALDO:", e.negrita), ""],
        [saldo, ""],
    ]
    if r.observaciones:
        filas.append([_campo("Observaciones:", r.observaciones), ""])
    filas.append([_p("f: ________________________________   RECIBIDO", e.centro), ""])
    if r.anulado:
        filas.append(
            [
                Paragraph(
                    f"<font color='#b91c1c'><b>RECIBO ANULADO</b> — "
                    f"{escape(r.motivo_anulacion or '')}</font>",
                    e.centro,
                ),
                "",
            ]
        )

    t = Table(filas, colWidths=[ANCHO * 0.8, ANCHO * 0.2])
    estilo = [
        ("BOX", (0, 0), (-1, -1), 0.8, e.AZUL),
        ("SPAN", (0, 0), (1, 0)),
        ("SPAN", (0, 1), (1, 1)),
        ("ALIGN", (0, 1), (-1, 1), "RIGHT"),
        ("SPAN", (0, 3), (1, 3)),
        ("SPAN", (0, 4), (1, 4)),
        ("LINEABOVE", (0, 5), (-1, 5), 0.4, e.GRIS),
        ("LINEABOVE", (0, 7), (-1, 7), 0.4, e.GRIS),
        ("SPAN", (0, 8), (1, 8)),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]
    for i in range(9, len(filas)):
        estilo.append(("SPAN", (0, i), (1, i)))
    t.setStyle(TableStyle(estilo))
    return t


def construir_recibo(recibo: ReciboLeer, config: ConfiguracionDatos) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=e.MARGEN,
        rightMargin=e.MARGEN,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=f"Recibo de Caja {recibo.numero_formateado}",
        author=config.empresa,
        subject=f"Promesa {recibo.contrato_numero:05d} — Lote {recibo.lotes_texto}",
        creator="Sistema Documental",
    )
    corte = _p("- " * 70 + " cortar aquí", e.pequeno)
    doc.build(
        [
            _bloque(recibo, config, "ORIGINAL — CLIENTE"),
            Spacer(1, 6 * mm),
            corte,
            Spacer(1, 6 * mm),
            _bloque(recibo, config, "COPIA — CAJA"),
        ]
    )
    return buffer.getvalue()
