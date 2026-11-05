---
name: generar-pdf
description: Generar y descargar PDFs del sistema — factura imprimible, contrato, ficha de plano/terreno, reportes/listados, expediente completo (unir documento generado + archivos originales) y descarga masiva en ZIP. Usar al implementar cualquier endpoint o botón de "Descargar PDF" o al diseñar plantillas de documentos.
---

# Generar y descargar PDF

Requisito central del proyecto: **todo** (facturas, contratos, planos, reportes) debe poder descargarse en PDF.

## Tecnologías

- **ReportLab (platypus)** para componer documentos: puro Python, funciona en Windows sin dependencias nativas.
- **pypdf** para unir el PDF generado con los PDFs originales subidos (expediente), añadir metadatos, marcas de agua.
- **pypdfium2** para convertir imágenes de planos (JPG/PNG) → se insertan con `reportlab.platypus.Image`.
- **qrcode** (opcional) para QR de verificación en facturas.

## Arquitectura (en `backend/app/pdf/`)

```
pdf/
  generacion.py        # funciones puras: datos (schemas Pydantic) -> bytes PDF
  estilos.py           # paleta, fuentes, márgenes, encabezado/pie comunes
  plantillas/
    factura.py         # construir_factura(factura: FacturaDetalle) -> bytes
    contrato.py
    plano.py           # ficha técnica del terreno + plano embebido
    reporte.py         # listados tabulares con filtros aplicados
  expediente.py        # unir generado + adjuntos originales con pypdf
```

Reglas:
1. Las plantillas **reciben schemas ya validados**, nunca modelos ORM ni sesiones de BD. Así son testeables sin BD.
2. Devuelven `bytes`; el router decide cómo entregarlos.
3. Registrar fuente con soporte de tildes/ñ: `pdfmetrics.registerFont(TTFont("DejaVuSans", ruta))` — las fuentes estándar Helvetica no cubren todo; guardar el .ttf en `backend/app/pdf/fuentes/`.
4. Montos con `Decimal` formateados `Q 1,234.56`; fechas `dd/mm/aaaa`; montos en letras en contratos (función `numero_a_letras`).
5. Encabezado con nombre de la empresa/logo, pie con "Página X de Y", fecha de generación y usuario que generó.
6. Metadatos del PDF: `title`, `author`, `subject`, `creator="Sistema Documental"`.
7. Facturas que no sean FEL certificadas deben llevar la leyenda **"Documento de control interno — no válido como factura fiscal"** salvo que se imprima la representación gráfica oficial del DTE.

## Endpoint de descarga (patrón FastAPI)

```python
@router.get("/{factura_id}/pdf")
def descargar_factura_pdf(factura_id: int, usuario=Depends(usuario_actual), db=Depends(get_db)):
    factura = servicio.obtener_detalle(db, factura_id, usuario)   # valida permisos -> 404/403
    contenido = plantillas.factura.construir_factura(factura)
    auditoria.registrar(db, usuario, "descargar_pdf", "factura", factura_id)
    nombre = f"factura_{factura.serie}_{factura.numero}.pdf"
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"',
                 "Cache-Control": "no-store"},
    )
```

- `inline` en vez de `attachment` para vista previa en el navegador.
- PDFs grandes o expedientes → `StreamingResponse` o generar en segundo plano y guardar en `storage/generados/` con caducidad.
- **Descarga masiva:** `zipfile.ZipFile` en memoria (`io.BytesIO`) con un PDF por documento + `indice.csv`; limitar a N documentos por petición.

## Frontend

```ts
const r = await api.get(`/facturas/${id}/pdf`, { responseType: "blob" });
const url = URL.createObjectURL(r.data);
const a = Object.assign(document.createElement("a"), { href: url, download: nombreDesdeHeader(r) });
a.click(); URL.revokeObjectURL(url);
```
Mostrar estado de carga en el botón y error amigable si falla. Vista previa con `<iframe src={url}>`.

## Validación de un PDF generado (tests)

```python
def test_pdf_factura_se_genera():
    pdf = construir_factura(factura_ejemplo())
    assert pdf.startswith(b"%PDF-")
    lector = PdfReader(io.BytesIO(pdf))
    texto = lector.pages[0].extract_text()
    assert "Q 1,120.00" in texto and factura_ejemplo().nit_receptor in texto
```
Además, revisar visualmente: guardar en el scratchpad y abrirlo con la herramienta Read (lee PDFs) o `extraer_pdf.py`.

Ver `plantilla-factura-ejemplo.py` para una plantilla base funcional.
