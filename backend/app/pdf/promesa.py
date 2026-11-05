"""PDF de la Promesa de Compra Venta.

Página 1: datos (réplica del formulario en papel). Página 2: condiciones generales.
Página 3: anexo con el plan de pagos. Recibe schemas validados y devuelve bytes (sin BD).
"""

import io
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core import formato as f
from app.modules.clientes.schemas import PersonaDatos
from app.modules.configuracion.models import ConfiguracionDatos
from app.modules.configuracion.textos import CONDICIONES_GENERALES, condiciones_para
from app.modules.contratos.schemas import ContratoLeer
from app.modules.lotes.schemas import nombre_lotificacion
from app.pdf import estilos as e

ANCHO = LETTER[0] - 2 * e.MARGEN
BLANCO = "_" * 18


def _p(texto: object, estilo=e.base) -> Paragraph:
    return Paragraph(escape("" if texto is None else str(texto)), estilo)


def _seccion(titulo: str) -> Table:
    t = Table([[Paragraph(titulo, e.titulo_seccion)]], colWidths=[ANCHO])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), e.AZUL),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ]
        )
    )
    return t


def _filas_pares(izq: list[tuple[str, object]], der: list[tuple[str, object]]) -> Table:
    filas = []
    for i in range(max(len(izq), len(der))):
        a = izq[i] if i < len(izq) else ("", "")
        b = der[i] if i < len(der) else ("", "")
        filas.append([_p(a[0], e.negrita), _p(a[1]), _p(b[0], e.negrita), _p(b[1])])
    ancho_etq, ancho_val = 38 * mm, ANCHO / 2 - 38 * mm
    t = Table(filas, colWidths=[ancho_etq, ancho_val, ancho_etq, ancho_val])
    t.setStyle(e.TABLA_DATOS)
    return t


def _persona(p: PersonaDatos | None, fecha_ref) -> list[tuple[str, object]]:
    if p is None:
        return []
    return [
        ("NOMBRES Y APELLIDOS:", p.nombres_apellidos),
        ("DIRECCIÓN:", p.direccion),
        ("TELÉFONO:", p.telefono),
        ("D.P.I.:", p.dpi),
        ("CORREO:", p.email),
        ("FECHA DE NACIMIENTO:", f.fecha_corta(p.fecha_nacimiento)),
        ("EDAD:", f.edad(p.fecha_nacimiento, fecha_ref)),
        ("NACIONALIDAD:", p.nacionalidad),
        ("PROFESIÓN:", p.profesion_actividad),
    ]


def _cuentas(cfg: ConfiguracionDatos) -> list:
    if not cfg.cuentas_bancarias:
        return []
    detalle = "; ".join(
        f"{x.banco}, CUENTA DE {x.tipo} No. {x.numero} A NOMBRE DE {x.titular}"
        for x in cfg.cuentas_bancarias
    )
    return [
        _p(f"LOS PAGOS PUEDEN DEPOSITARSE EN LAS CUENTAS: {detalle}.", e.justificado),
        Spacer(1, 1.5 * mm),
    ]


def _pagina_datos(c: ContratoLeer, cfg: ConfiguracionDatos) -> list:
    cond = c.condiciones
    comp = c.comprador
    t = comp.trabajo
    proyecto = nombre_lotificacion(c.lotificacion, cfg.proyecto)

    encabezado = Table(
        [
            [
                [
                    Paragraph(escape(proyecto), e.encabezado_empresa),
                    _p(cfg.empresa, e.negrita),
                    _p(
                        f"OFICINAS: {cfg.direccion_oficinas} — Tel. {cfg.telefono_oficinas}",
                        e.pequeno,
                    ),
                    _p(f"PROYECTO: {cfg.direccion_proyecto}", e.pequeno),
                ],
                [
                    Paragraph("PROMESA DE<br/>COMPRA VENTA", e.titulo_documento),
                    Paragraph(
                        f"<font size=14 color='#b91c1c'>Nº {c.numero_formateado}</font>",
                        e.titulo_documento,
                    ),
                ],
            ]
        ],
        colWidths=[ANCHO * 0.68, ANCHO * 0.32],
    )
    encabezado.setStyle(
        TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOX", (1, 0), (1, 0), 0.8, e.AZUL)])
    )

    persona = _persona(comp, c.fecha_firma)
    comprador = [
        *persona[:4],
        ("N.I.T.:", comp.nit),
        *persona[4:],
        ("ESTADO CIVIL:", comp.estado_civil),
        ("DEPENDIENTES:", comp.num_dependientes),
    ]
    conyuge = _persona(c.conyuge_gestor, c.fecha_firma)
    titulos = Table(
        [
            [
                _p("DATOS DEL COMPRADOR", e.negrita),
                _p("DATOS DEL CÓNYUGE, FAMILIAR O GESTOR", e.negrita),
            ]
        ],
        colWidths=[ANCHO / 2, ANCHO / 2],
    )

    elementos: list = [
        encabezado,
        Spacer(1, 2 * mm),
        _seccion("DATOS GENERALES DEL PROMITENTE COMPRADOR Y DEL CÓNYUGE"),
        titulos,
        _filas_pares(comprador, conyuge),
        Spacer(1, 1.5 * mm),
        _seccion("DATOS LABORALES DEL COMPRADOR"),
        _filas_pares(
            [("EMPRESA:", t.empresa), ("DIRECCIÓN:", t.direccion), ("TELÉFONO:", t.telefono)],
            [
                ("PUESTO:", t.puesto),
                ("TIEMPO DE TRABAJO:", t.tiempo_trabajo),
                ("INGRESO MENSUAL:", f.moneda(t.ingreso_mensual)),
                ("OTROS INGRESOS:", f.moneda(t.otros_ingresos)),
            ],
        ),
    ]

    if c.dependientes:
        filas = [["Nombre de las personas que dependen de él", "Edad", "No. de DPI"]]
        filas += [[_p(d.nombre), d.edad or "", d.dpi or ""] for d in c.dependientes]
        tabla = Table(filas, colWidths=[ANCHO * 0.6, ANCHO * 0.1, ANCHO * 0.3])
        tabla.setStyle(e.TABLA_GRILLA)
        elementos += [Spacer(1, 1.5 * mm), tabla]

    lote = c.lote
    elementos += [
        Spacer(1, 2 * mm),
        _seccion("IDENTIFICACIÓN DEL INMUEBLE"),
        _filas_pares(
            [("LOTE No.:", lote.codigo), ("FINCA No.:", lote.finca), ("FOLIO No.:", lote.folio)],
            [
                ("ÁREA TOTAL:", f"{f.numero(lote.area_m2)} METROS CUADRADOS"),
                ("LIBRO No.:", lote.libro),
                ("DE:", lote.libro_de),
            ],
        ),
        Spacer(1, 2 * mm),
        _seccion("CONDICIONES DE LA COMPRA-VENTA AL CONTADO O FINANCIADO"),
    ]

    montos = [
        ["PRECIO DEL TERRENO", f.moneda(cond.precio_terreno)],
        ["MEJORAS AL TERRENO", f.moneda(cond.mejoras)],
        ["TOTAL", f.moneda(cond.total)],
        ["(-) ENGANCHE", f.moneda(cond.enganche)],
        ["(-) OTROS DESCUENTOS", f.moneda(cond.otros_descuentos)],
        ["SALDO A PAGAR", f.moneda(cond.saldo_a_pagar)],
    ]
    fracciones = [["ENGANCHE FRACCIONADO", ""], ["FECHA", "MONTO"]]
    fracciones += [[f.fecha_corta(x.fecha), f.moneda(x.monto)] for x in cond.enganche_fraccionado]
    fracciones += [["", ""]] * (6 - len(fracciones))
    tabla_montos = Table(montos, colWidths=[ANCHO * 0.3, ANCHO * 0.2])
    tabla_montos.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEBELOW", (1, 0), (1, -1), 0.3, e.GRIS),
                ("LINEABOVE", (0, 2), (-1, 2), 0.6, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 1.2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
            ]
        )
    )
    tabla_fracciones = Table(fracciones, colWidths=[ANCHO * 0.25, ANCHO * 0.23])
    tabla_fracciones.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (-1, 0)),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LINEBELOW", (0, 2), (-1, -1), 0.3, e.GRIS),
                ("TOPPADDING", (0, 0), (-1, -1), 1.2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
            ]
        )
    )
    doble = Table([[tabla_montos, tabla_fracciones]], colWidths=[ANCHO * 0.52, ANCHO * 0.48])
    doble.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))

    anios = "AÑO" if cond.plazo_anios == 1 else "AÑOS"
    reglas = cfg.reglas
    firma = c.fecha_firma
    elementos += [
        doble,
        Spacer(1, 2 * mm),
        _p(
            f"EL SALDO A PAGAR MÁS SUS INTERESES SE PAGARÁ EN {cond.plazo_anios} {anios} PLAZO, "
            f"MEDIANTE {cond.numero_cuotas} CUOTAS NIVELADAS MENSUALES (CAPITAL E INTERESES) DE "
            f"{f.moneda(cond.cuota_nivelada)}; APLICÁNDOSE UNA TASA DE INTERÉS ANUAL VARIABLE DEL "
            f"{f.numero(cond.tasa_interes_anual_pct)}% INICIAL, DEBIENDO CANCELAR LA PRIMERA CUOTA "
            f"EL DÍA {f.fecha_corta(cond.fecha_primera_cuota)} Y LAS SIGUIENTES LOS DÍAS "
            f"{cond.dia_pago_mensual} DE CADA MES.",
            e.justificado,
        ),
        Spacer(1, 1.5 * mm),
        _p(
            f"OTRAS CONDICIONES DE LA NEGOCIACIÓN: {cond.otras_condiciones or BLANCO * 3}",
            e.justificado,
        ),
        Spacer(1, 1.5 * mm),
        *_cuentas(cfg),
        _p(
            f"EN CASO QUE EL PROMITENTE COMPRADOR RESCINDA LA COMPRA DEL INMUEBLE, PERDERÁ A FAVOR "
            f"DE {cfg.empresa} Y/O {proyecto}, EN CONCEPTO DE ARRAS, LA CANTIDAD EQUIVALENTE "
            f"AL {f.numero(reglas.arras_pct_precio)}% DEL PRECIO DE VENTA DEL INMUEBLE, O EL "
            f"{f.numero(reglas.arras_pct_pagado)}% DEL MONTO PAGADO A LA FECHA DEL DESISTIMIENTO, "
            "LA QUE SEA MAYOR. AMBAS PARTES, PROMITENTE Y PROMISARIO, ACEPTAN TODAS Y CADA UNA DE "
            "LAS CONDICIONES QUE SE ENCUENTRAN EN ESTE DOCUMENTO PROVISIONAL, HASTA QUE EL "
            "PROMISARIO ELEVE A ESCRITURA PÚBLICA ESTE CONTRATO EN FORMA DEFINITIVA.",
            e.justificado,
        ),
        Spacer(1, 1.5 * mm),
        _p(
            f"EN FE DE LO CUAL, FIRMAN DE CONFORMIDAD EL PRESENTE DOCUMENTO, EL DÍA {firma.day} DE "
            f"{f.mes_nombre(firma)} DE {f.anio_en_letras(firma.year)}.",
            e.justificado,
        ),
        Spacer(1, 11 * mm),
    ]

    firmas = Table(
        [
            ["(F) ______________________________", "(F) ______________________________"],
            [_p(comp.nombres_apellidos, e.centro), _p(cfg.representante_legal, e.centro)],
            ["COMPRADOR", "PROPIETARIO"],
        ],
        colWidths=[ANCHO / 2, ANCHO / 2],
    )
    firmas.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
            ]
        )
    )
    elementos += [firmas, Spacer(1, 3 * mm)]

    n = c.notario
    ciudad = (n.ciudad if n and n.ciudad else None) or BLANCO
    fecha_n = n.fecha if n and n.fecha else None
    dia = str(fecha_n.day) if fecha_n else BLANCO[:8]
    mes = f.mes_nombre(fecha_n) if fecha_n else BLANCO
    anio = f.anio_en_letras(fecha_n.year) if fecha_n else f"DOS MIL {BLANCO[:10]}"
    representante = (n.representante if n and n.representante else None) or (
        cfg.representante_legal or BLANCO * 2
    )
    elementos.append(
        _p(
            f"EN LA CIUDAD DE {ciudad}, A LOS {dia} DÍAS DEL MES DE {mes} DEL AÑO {anio}, YO, EL "
            "INFRASCRITO NOTARIO, DOY FE QUE LAS FIRMAS QUE ANTECEDEN A LA PRESENTE RAZÓN, SON "
            "AUTÉNTICAS POR HABER SIDO PUESTAS EN MI PRESENCIA EL DÍA DE HOY POR LA SEÑOR(A) "
            f"{representante} EN REPRESENTACIÓN DE {cfg.empresa} Y POR EL (LA) SEÑOR(A) "
            f"{comp.nombres_apellidos}, QUIENES SE IDENTIFICAN CON LOS DOCUMENTOS PERSONALES DE "
            "IDENTIFICACIÓN RELACIONADOS EN EL PRESENTE DOCUMENTO.",
            e.pequeno,
        )
    )
    return elementos


def _pagina_condiciones(c: ContratoLeer, cfg: ConfiguracionDatos) -> list:
    elementos: list = [
        Paragraph("PROMESA DE COMPRA – VENTA<br/>CONDICIONES GENERALES", e.titulo_documento),
        Spacer(1, 3 * mm),
    ]
    if not cfg.condiciones_generales_validadas:
        elementos.append(
            _p(
                "BORRADOR — El texto de estas condiciones generales está pendiente de validar "
                "contra el documento original. No usar para firma.",
                e.negrita,
            )
        )
        elementos.append(Spacer(1, 2 * mm))
    for titulo, texto in condiciones_para(c.lotificacion, CONDICIONES_GENERALES):
        cuerpo = f": {escape(texto)}" if texto else ""
        elementos.append(Paragraph(f"<b>{escape(titulo)}</b>{cuerpo}", e.clausula))
    elementos += [
        Spacer(1, 12 * mm),
        Table(
            [["(F) ______________________________"], ["COMPRADOR"]],
            colWidths=[ANCHO],
            style=[
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ],
        ),
    ]
    return elementos


def _pagina_plan(c: ContratoLeer) -> list:
    filas = [["No.", "Vencimiento", "Capital", "Interés", "Cuota", "Saldo"]]
    filas += [
        [
            q.numero,
            f.fecha_corta(q.vencimiento),
            f.numero(q.capital),
            f.numero(q.interes),
            f.numero(q.cuota),
            f.numero(q.saldo_despues),
        ]
        for q in c.plan_cuotas
    ]
    tabla = Table(
        filas, colWidths=[ANCHO * x for x in (0.08, 0.18, 0.185, 0.185, 0.185, 0.185)], repeatRows=1
    )
    tabla.setStyle(e.TABLA_GRILLA)
    tabla.setStyle(
        TableStyle([("ALIGN", (2, 1), (-1, -1), "RIGHT"), ("ALIGN", (0, 0), (1, -1), "CENTER")])
    )
    return [
        Paragraph(f"ANEXO — PLAN DE PAGOS · PROMESA Nº {c.numero_formateado}", e.titulo_documento),
        Spacer(1, 2 * mm),
        _p(
            f"Comprador: {c.comprador.nombres_apellidos} · Lote {c.lote.codigo} · Saldo "
            f"financiado {f.moneda(c.condiciones.saldo_a_pagar)} · Tasa anual "
            f"{f.numero(c.condiciones.tasa_interes_anual_pct)}%",
            e.centro,
        ),
        Spacer(1, 3 * mm),
        tabla,
    ]


def construir_promesa(contrato: ContratoLeer, config: ConfiguracionDatos) -> bytes:
    buffer = io.BytesIO()
    generado = datetime.now(UTC).strftime("%d/%m/%Y %H:%M UTC")

    def pie(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(e.GRIS)
        canvas.drawString(
            e.MARGEN, 7 * mm, f"Promesa de Compra Venta Nº {contrato.numero_formateado}"
        )
        canvas.drawRightString(
            LETTER[0] - e.MARGEN, 7 * mm, f"Página {doc.page} · generado {generado}"
        )
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=e.MARGEN,
        rightMargin=e.MARGEN,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
        title=f"Promesa de Compra Venta {contrato.numero_formateado}",
        author=config.empresa,
        subject=f"Lote {contrato.lote.codigo}",
        creator="Sistema Documental",
    )
    historia = [
        *_pagina_datos(contrato, config),
        PageBreak(),
        *_pagina_condiciones(contrato, config),
    ]
    if contrato.plan_cuotas:
        historia += [PageBreak(), *_pagina_plan(contrato)]
    doc.build(historia, onFirstPage=pie, onLaterPages=pie)
    return buffer.getvalue()
