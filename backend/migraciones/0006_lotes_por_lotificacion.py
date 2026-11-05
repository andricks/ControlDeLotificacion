"""El número de lote es único por lotificación (Monaco, Finca El Ensueño, Tablon Campestre2).

Quita el índice único antiguo sobre `codigo`; Beanie crea al arrancar el nuevo índice único
(lotificacion, codigo). Los lotes y promesas existentes quedan sin lotificación (sus PDFs usan
el nombre de configuración, como hasta ahora).
"""

INDICE_ANTERIOR = "codigo_1"
INDICE_NUEVO = "lotificacion_1_codigo_1"


async def _indices(db) -> set[str]:
    return set(await db["lotes"].index_information())


async def aplicar(db) -> None:
    if INDICE_ANTERIOR in await _indices(db):
        await db["lotes"].drop_index(INDICE_ANTERIOR)


async def revertir(db) -> None:
    # Falla si ya hay el mismo número de lote en dos lotificaciones (habría que resolverlo antes).
    if INDICE_NUEVO in await _indices(db):
        await db["lotes"].drop_index(INDICE_NUEVO)
    await db["lotes"].create_index("codigo", unique=True, name=INDICE_ANTERIOR)
