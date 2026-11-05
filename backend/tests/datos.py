"""Datos de prueba FICTICIOS con la estructura y montos del contrato real (sin datos personales)."""

from copy import deepcopy

DPI_COMPRADOR = "1234567892101"
DPI_CONYUGE = "8765432122101"

_CONTRATO = {
    "fecha_firma": "2025-01-22",
    "lotificacion": "tablon_campestre2",
    "comprador": {
        "nombres_apellidos": "Juan Carlos Pérez Muñoz",
        "dpi": DPI_COMPRADOR,
        "nit": "1234567-9",
        "direccion": "Colonia Ejemplo zona 1, Jalapa",
        "telefono": "5555-0000",
        "fecha_nacimiento": "1976-02-12",
        "nacionalidad": "Guatemalteca",
        "estado_civil": "Casado",
        "num_dependientes": 1,
        "profesion_actividad": "Comerciante",
        "trabajo": {
            "empresa": "Negocio propio",
            "puesto": "Propietario",
            "tiempo_trabajo": "15 años",
            "ingreso_mensual": "15000.00",
            "otros_ingresos": "0.00",
        },
    },
    "conyuge_gestor": {
        "nombres_apellidos": "María José López Ramírez",
        "dpi": DPI_CONYUGE,
        "direccion": "Colonia Ejemplo zona 1, Jalapa",
        "fecha_nacimiento": "2000-05-03",
    },
    "lote": {
        "codigo": "36-b34",
        "area_m2": "144.00",
        "finca": "0000",
        "folio": "00",
        "libro": "00E",
        "libro_de": "Jalapa",
    },
    "condiciones": {
        "precio_terreno": "20000.00",
        "mejoras": "102400.00",
        "enganche": "10000.00",
        "otros_descuentos": "0.00",
        "enganche_fraccionado": [{"fecha": "2025-01-22", "monto": "10000.00"}],
        "plazo_anios": 1,
        "numero_cuotas": 11,
        "tasa_interes_anual_pct": "0",
        "fecha_primera_cuota": "2025-02-28",
        "dia_pago_mensual": 30,
        "otras_condiciones": "Plan semicontado pagando cada 30 del mes.",
    },
}


def contrato_ejemplo(**cambios) -> dict:
    datos = deepcopy(_CONTRATO)
    for ruta, valor in cambios.items():
        destino = datos
        *padres, hoja = ruta.split("__")
        for p in padres:
            destino = destino[p]
        destino[hoja] = valor
    return datos
