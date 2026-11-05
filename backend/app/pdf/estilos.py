"""Estilos comunes de los PDFs. Helvetica (WinAnsi) cubre tildes y ñ del español."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import TableStyle

AZUL = colors.HexColor("#1e3a5f")
GRIS = colors.HexColor("#6b7280")
GRIS_CLARO = colors.HexColor("#e5e7eb")

MARGEN = 12 * mm

base = ParagraphStyle("base", fontName="Helvetica", fontSize=7.5, leading=9.2)
negrita = ParagraphStyle("negrita", parent=base, fontName="Helvetica-Bold")
justificado = ParagraphStyle("justificado", parent=base, alignment=TA_JUSTIFY)
pequeno = ParagraphStyle("pequeno", parent=base, fontSize=6.5, leading=8, textColor=GRIS)
centro = ParagraphStyle("centro", parent=base, alignment=TA_CENTER)
centro_pequeno = ParagraphStyle("centro_pequeno", parent=pequeno, alignment=TA_CENTER)
titulo_seccion = ParagraphStyle(
    "titulo_seccion",
    parent=base,
    fontName="Helvetica-Bold",
    fontSize=8,
    textColor=colors.white,
    alignment=TA_CENTER,
)
encabezado_empresa = ParagraphStyle(
    "encabezado_empresa",
    parent=base,
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=15,
    textColor=AZUL,
)
titulo_documento = ParagraphStyle(
    "titulo_documento",
    parent=base,
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=13,
    alignment=TA_CENTER,
)
clausula = ParagraphStyle("clausula", parent=justificado, fontSize=7, leading=8.6, spaceAfter=3)

TABLA_DATOS = TableStyle(
    [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (1, 0), (1, -1), 0.3, GRIS),
        ("LINEBELOW", (3, 0), (3, -1), 0.3, GRIS),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
    ]
)

TABLA_GRILLA = TableStyle(
    [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
        ("GRID", (0, 0), (-1, -1), 0.3, GRIS),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]
)
