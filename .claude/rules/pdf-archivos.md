---
paths:
  - "backend/app/pdf/**"
  - "backend/app/modules/archivos/**"
  - "backend/app/core/almacenamiento.py"
---

# Reglas: PDF y archivos

- Validar tipo por magic bytes (`%PDF-`, PNG, JPEG, TIFF), tamaño máximo configurable, y calcular SHA-256.
- Nombre interno `uuid4` + extensión derivada del tipo real; el nombre original solo se guarda en BD y se sanea al descargar.
- Nunca construir rutas de disco con texto del usuario; todo acceso pasa por `core/almacenamiento.py`.
- Si falla el commit tras guardar un archivo, borrar el archivo (sin huérfanos).
- Plantillas PDF reciben schemas validados y devuelven `bytes`; no acceden a la BD.
- Fuentes: Helvetica de ReportLab (WinAnsi) cubre tildes y ñ; registrar una TTF solo si se necesitan caracteres fuera de Latin-1. Estilos comunes en `app/pdf/estilos.py`.
- Todo texto dinámico en `Paragraph` pasa por `xml.sax.saxutils.escape` (ReportLab interpreta etiquetas).
- Tras cambiar una plantilla, renderizar a PNG (pypdfium2) en el scratchpad y revisarla visualmente.
- OCR y PDFs grandes → tarea en segundo plano, no en el request.
- Cada plantilla nueva tiene un test que verifica `%PDF-` y la presencia de los datos clave en el texto extraído.
- Documentos no fiscales llevan la leyenda "Documento de control interno — no válido como factura fiscal".
