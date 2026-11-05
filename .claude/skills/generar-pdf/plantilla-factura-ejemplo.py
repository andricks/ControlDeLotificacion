"""Plantilla base de factura con ReportLab (referencia para backend/app/pdf/plantillas/factura.py).

Ejecutar para probar:  python plantilla-factura-ejemplo.py salida.pdf
Requiere: pip install reportlab
"""

from __future__ import annotations

import io
import sys
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

IVA = Decimal("0.12")
DOS = Decimal("0.01")


@dataclass
class Linea:
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal  # IVA incluido

    @property
    def subtotal(self) -> Decimal:
        return (self.cantidad * self.precio_unitario).quantize(DOS, ROUND_HALF_UP)


@dataclass
class FacturaDemo:
    serie: str
    numero: str
    fecha: date
    emisor: str
    nit_emisor: str
    receptor: str
    nit_receptor: str
    lineas: list[Linea] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return sum((l.subtotal for l in self.lineas), Decimal("0"))

    @property
    def iva(self) -> Decimal:
        return (self.total / (1 + IVA) * IVA).quantize(DOS, ROUND_HALF_UP)


def q(monto: Decimal) -> str:
    return f"Q {monto:,.2f}"


def construir_factura(f: FacturaDemo) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title=f"Factura {f.serie}-{f.numero}", author=f.emisor,
                            creator="Sistema Documental")
    est = getSampleStyleSheet()
    pequeno = ParagraphStyle("pequeno", parent=est["Normal"], fontSize=8, textColor=colors.grey)
    elementos = [
        Paragraph(f"<b>{f.emisor}</b>", est["Title"]),
        Paragraph(f"NIT: {f.nit_emisor}", est["Normal"]),
        Spacer(1, 6 * mm),
        Table([["Serie", f.serie, "Número", f.numero],
               ["Fecha", f.fecha.strftime("%d/%m/%Y"), "NIT receptor", f.nit_receptor],
               ["Receptor", f.receptor, "", ""]],
              colWidths=[25 * mm, 60 * mm, 30 * mm, 60 * mm],
              style=TableStyle([("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                                ("SPAN", (1, 2), (3, 2))])),
        Spacer(1, 6 * mm),
    ]
    filas = [["Cant.", "Descripción", "P. unitario", "Subtotal"]]
    filas += [[f"{l.cantidad:g}", Paragraph(l.descripcion, est["Normal"]), q(l.precio_unitario),
               q(l.subtotal)] for l in f.lineas]
    filas += [["", "", "IVA incluido (12 %)", q(f.iva)], ["", "", "TOTAL", q(f.total)]]
    elementos.append(Table(filas, colWidths=[18 * mm, 92 * mm, 35 * mm, 35 * mm], repeatRows=1,
                           style=TableStyle([
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                               ("GRID", (0, 0), (-1, -3), 0.4, colors.grey),
                               ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")])))
    elementos += [Spacer(1, 10 * mm),
                  Paragraph("Documento de control interno — no válido como factura fiscal.", pequeno)]

    def pie(canvas, documento):
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(LETTER[0] - 18 * mm, 10 * mm, f"Página {documento.page}")

    doc.build(elementos, onFirstPage=pie, onLaterPages=pie)
    return buf.getvalue()


if __name__ == "__main__":
    demo = FacturaDemo("A1B2C3D4", "000123", date.today(), "Inmobiliaria Ejemplo, S.A.", "1234567-9",
                       "Consumidor Final", "CF",
                       [Linea("Medición topográfica de lote", Decimal("1"), Decimal("1500.00")),
                        Linea("Copia certificada de plano", Decimal("2"), Decimal("75.50"))])
    salida = sys.argv[1] if len(sys.argv) > 1 else "factura_demo.pdf"
    with open(salida, "wb") as fh:
        fh.write(construir_factura(demo))
    print(f"Generado {salida} — total {q(demo.total)}, IVA {q(demo.iva)}")
