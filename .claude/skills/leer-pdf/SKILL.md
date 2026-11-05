---
name: leer-pdf
description: Leer y extraer información de archivos PDF (facturas, contratos, planos) — texto, tablas, metadatos, número de páginas, miniaturas y OCR para escaneos. Usar cuando haya que analizar un PDF que el usuario comparte, implementar la extracción automática de datos al subir documentos, o depurar por qué un PDF no se lee bien.
---

# Leer PDF

## Uso rápido (inspeccionar un PDF durante el desarrollo)

```powershell
python .claude/skills/leer-pdf/scripts/extraer_pdf.py "ruta\archivo.pdf"            # resumen + texto
python .claude/skills/leer-pdf/scripts/extraer_pdf.py "ruta\archivo.pdf" --json     # salida estructurada
python .claude/skills/leer-pdf/scripts/extraer_pdf.py "ruta\archivo.pdf" --tablas   # incluye tablas
python .claude/skills/leer-pdf/scripts/extraer_pdf.py "ruta\archivo.pdf" --paginas 1-3
python .claude/skills/leer-pdf/scripts/extraer_pdf.py "ruta\archivo.pdf" --miniatura salida.png
```

Dependencias: `pip install pdfplumber pypdf pypdfium2` (OCR opcional: `pip install pytesseract` + instalar Tesseract con idioma `spa`).
Si solo necesitas *ver* el PDF, la herramienta Read de Claude Code también lee PDFs (parámetro `pages`, máx. 20 por llamada).

## Qué librería usar

| Tarea | Librería | Motivo |
|---|---|---|
| Texto con posición, tablas | `pdfplumber` | Mejor extracción de tablas (facturas con líneas de detalle) |
| Metadatos, páginas, unir/dividir, cifrado | `pypdf` | Puro Python, estable |
| Renderizar página → imagen (miniaturas, vista previa de planos) | `pypdfium2` | Rápido, licencia permisiva (evitar PyMuPDF: AGPL) |
| PDF escaneado sin capa de texto | `pytesseract` sobre imagen de `pypdfium2` | OCR en español (`lang="spa"`) |

## Algoritmo de extracción (implementar en `backend/app/pdf/lectura.py`)

1. **Validar** antes de abrir: magic bytes `%PDF-`, tamaño ≤ límite configurado, no cifrado (o pedir contraseña).
2. **Metadatos** con pypdf: páginas, autor, fecha de creación, productor.
3. **Texto** con pdfplumber por página. Si una página tiene < 20 caracteres útiles → probablemente escaneada → marcar `requiere_ocr=True`.
4. **OCR** (solo si está habilitado): renderizar a 300 DPI con pypdfium2 → `pytesseract.image_to_string(img, lang="spa")`. Es lento: ejecutar en tarea en segundo plano, nunca en el request.
5. **Normalizar** texto: `unicodedata.normalize("NFC")`, colapsar espacios, conservar saltos de línea.
6. **Guardar** en `archivos.texto_extraido` (para búsqueda de texto completo) y el resultado de campos detectados en JSON aparte con nivel de confianza.
7. **Nunca** confiar ciegamente en los datos extraídos: se proponen al usuario en el formulario para que los confirme.

## Extracción de campos por tipo de documento

Ver `referencia-campos.md` para expresiones regulares y heurísticas de:
- **Factura FEL (Guatemala):** serie, número DTE, número de autorización (UUID), NIT emisor/receptor, fecha, total, IVA.
- **Contrato:** tipo, partes, DPI, fecha de firma, monto, número de finca/folio/libro.
- **Plano:** finca, folio, libro, área (m², varas², manzanas), escala, profesional y colegiado.

## Errores comunes

- PDF con fuentes sin mapa Unicode → texto con caracteres basura: caer a OCR.
- Tablas sin bordes → `page.extract_table({"vertical_strategy": "text", "horizontal_strategy": "text"})`.
- Planos grandes (A1/A0) → renderizar miniatura con `scale` bajo (≈0.3) para no agotar memoria.
- PDF dañado → capturar `pypdf.errors.PdfReadError` y responder 422 con mensaje claro.
- Nunca ejecutar JavaScript ni acciones embebidas del PDF; solo leer.
