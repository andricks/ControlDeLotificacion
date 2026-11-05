"""Condiciones generales de la Promesa de Compra Venta (dorso del formulario en papel).

Transcritas de la foto del documento original. Las cláusulas marcadas PENDIENTE no eran
legibles y deben completarse con el texto original antes de marcar
`condiciones_generales_validadas = True` en la configuración.
"""

OBRAS_URBANIZACION = "OBRAS DE URBANIZACIÓN INCLUIDAS EN EL PRECIO DEL LOTE"
DRENAJES = "2.Drenajes unicamente se permite Fosas Sépticas. "
LIMITACIONES_USO = "LIMITACIONES EN EL USO DEL LOTE"
USO_FOSAS = "d) Hacer uso adecuado del sistema de fosas septicas de aguas negras."

# Cambios de texto por lotificación: {lotificacion: {título de cláusula: (texto, reemplazo)}}.
VARIANTES: dict[str, dict[str, tuple[str, str]]] = {
    "monaco": {
        OBRAS_URBANIZACION: (DRENAJES, "2.Red de distribución de drenaje. "),
        LIMITACIONES_USO: (
            USO_FOSAS,
            "d) Hacer uso adecuado del sistema de drenaje de aguas negras.",
        ),
    },
}


def condiciones_para(
    lotificacion: str | None, clausulas: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    """Cláusulas con los cambios propios de la lotificación (las demás quedan igual)."""
    cambios = VARIANTES.get(lotificacion or "", {})
    resultado = []
    for titulo, texto in clausulas:
        if titulo in cambios:
            original, reemplazo = cambios[titulo]
            texto = texto.replace(original, reemplazo)
        resultado.append((titulo, texto))
    return resultado


CONDICIONES_GENERALES: list[tuple[str, str]] = [
    (
        "PROMESA DE COMPRA – VENTA",
        "El promitente comprador se obliga a comprar el inmueble en el precio, plazo y "
        "condiciones especificadas en este documento.",
    ),
    (
        "CUOTAS E INTERESES",
        "El promitente comprador se obliga a pagar el saldo pendiente de pago, a partir de la "
        "fecha indicada, en forma mensual, vencida y consecutiva en las oficinas del promitente "
        "vendedor, sin necesidad de cobro o requerimiento alguno. Los pagos mensuales se han "
        "calculado bajo el sistema de Cuotas Niveladas, que incluyen Capital e Intereses, "
        "aplicando una tasa de interés bancario (variable) anual, según condiciones ya "
        "estipuladas al dorso.",
    ),
    (
        "PAGOS A CAPITAL",
        "El promitente comprador podrá realizar pagos a cuenta del capital, NO menores de DOS MIL "
        "QUETZALES exactos, siempre y cuando se encuentre al día en sus pagos mensuales. El "
        "propósito de estos pagos será reducir el plazo y el pago de intereses, pero no para "
        "modificar el monto de la cuota nivelada mensual establecida.",
    ),
    (
        "RECARGOS POR MORA",
        "En caso el promitente comprador no haga efectivo los pagos respectivos, en las fechas "
        "convenidas, tendrá como margen para pagar los siguientes cinco días calendario. Después "
        "de esta fecha deberá pagar en concepto de recargo por mora un 5% mensual sobre cada "
        "cuota mensual vencida y por el número de meses atrasados de cada cuota.",
    ),
    (
        "PAGO",
        "El promitente comprador acepta que todos los pagos a que se refiere este contrato se "
        "harán efectivos sin necesidad de cobro o requerimiento alguno, en moneda de curso legal ",
    ),
    (
        "POSESIÓN DEL INMUEBLE",
        "El promitente comprador podrá tomar posesión del inmueble al momento de firmar la "
        "escritura traslativa de dominio.",
    ),
    (
        "TRASPASOS O DESISTIMIENTOS",
        "El promitente comprador podrá ceder su derecho de promitente a un tercero, siempre que "
        "el promitente vendedor dé su previa autorización escrita y que los pagos se encuentren "
        "al día; en caso de no darse la autorización, se procederá a devolver al promitente "
        "comprador el monto pagado por él, menos los gastos administrativos en los que haya "
        "incurrido el promitente vendedor. Los gastos que la operación de traspaso origine, "
        "incluyéndose en estos gastos el costo administrativo interno del promitente vendedor, "
        "son por cuenta del promitente comprador o tercero. En caso de desistimiento voluntario "
        "por parte del promitente comprador, deberá informarlo por escrito al promitente "
        "vendedor, quien resolverá de forma oportuna, estableciendo la penalidad respectiva, "
        "según lo estipulado al dorso.",
    ),
    (
        OBRAS_URBANIZACION,
        "El promitente comprador acepta que el promitente vendedor sólo entregue las siguientes "
        "obras de urbanización, de acuerdo a las especificaciones ya aprobadas por la "
        "municipalidad jurisdiccional: 1. Mojones señalando "
        f"{DRENAJES}"
        "3.Red de Distribución de Energía Eléctrica. 4. Red de Distribución del Agua, pozo "
        "propio. 5. El Servicio de Agua será suministrado por el proyecto, debiendo el "
        "promitente comprador cancelar en las oficinas del promitente vendedor el título "
        "respectivo que lo acredita dicho servicio, así también los gastos por conexión, "
        "instalación de su contador y canon de agua mensual correspondiente.",
    ),
    # PENDIENTE: texto de esta cláusula (sin texto, el PDF muestra solo el título).
    ("CARGOS NO INCLUIDOS EN EL PRECIO DEL LOTE", ""),
    (
        LIMITACIONES_USO,
        "El promitente comprador acepta y se obliga a observar las siguientes limitaciones: "
        "a) No subdividir el lote adquirido. b) Se autoriza el uso comercial del inmueble, "
        "siempre y cuando la actividad económica desarrollada no interfiera con la paz y el "
        "bienestar de los vecinos. Se prohíbe expresamente la operación de granjas, centros de "
        "acopio de desechos o cualquier negocio que produzca olores fétidos, humos o ruidos "
        "molestos. c) Avisar al promitente vendedor antes de construir para que este "
        f"verifique sus mojones y medidas y le establezca sus servicios. {USO_FOSAS}",
    ),
    (
        "INCUMPLIMIENTO DEL PROMITENTE COMPRADOR",
        "Si el promitente comprador incumpliere las obligaciones que adquiere, acepta que el "
        "promitente vendedor puede optar por lo siguiente: "
        "a) Obligar al promitente comprador a cumplir este contrato. "
        "b) Dejar sin efecto este contrato. "
        "c) El promitente vendedor podrá aceptar del promitente comprador la rescisión del "
        "contrato de promesa de compra-venta, siempre que la solicite por escrito y acepte que "
        "se deduzca de las sumas de dinero entregadas para el pago de su inmueble, una "
        "indemnización cuyo monto se determinará según lo establecido en el dorso de la presente.",
    ),
    (
        "CASOS EN QUE EL PROMITENTE VENDEDOR PODRÁ DEJAR SIN EFECTO ESTE CONTRATO",
        "El promitente comprador acepta que el promitente vendedor, sin necesidad de aviso o "
        "notificación, pueda dejar sin efecto la presente promesa de compra venta y disponer "
        "libremente del inmueble para ofrecerlo en venta a cualquier otra persona, en los casos "
        "siguientes: "
        "a) Si no cumpliere con pagar el enganche en la forma y plazos determinados en este "
        "contrato; "
        "b) Si llegare a tener en mora dos o más cuotas niveladas consecutivas; y "
        "c) Si no cumpliere con firmar la escritura de compra venta del inmueble en los 15 días "
        "posteriores a la fecha que se le hubiere citado para ello. "
        "En todos los casos el promitente vendedor podrá hacer suya una suma igual al 20% del "
        "precio de venta del inmueble o el 50% del monto pagado por el promitente comprador a la "
        "fecha del desistimiento, en concepto de multa. Descontada la multa, se devolverá al "
        "promitente comprador la cantidad que resulte a su favor.",
    ),
    (
        "DOMICILIO Y ACEPTACIÓN",
        "El promitente comprador acepta expresamente las condiciones contenidas en este documento "
        "y para su interpretación, cumplimiento y ejecución, las partes se someten a los "
        "Tribunales de la ciudad de Guatemala, salvo que por escrito hubieren señalado lugar "
        "distinto para todas las notificaciones, citaciones o avisos, que se hagan en la "
        "dirección señalada en el anverso de este contrato, además declara expresamente como "
        "líquido exigible y de plazo vencido la suma que pudiere demandársele, y como buenas y "
        "exactas las cuentas que el promitente vendedor le presente.",
    ),
]
