"""Extrae texto, tablas, metadatos y miniatura de un PDF.

Uso:
    python extraer_pdf.py archivo.pdf [--json] [--tablas] [--paginas 1-3] [--miniatura out.png] [--ocr]

Dependencias: pdfplumber, pypdf, pypdfium2 (opcional: pytesseract + Tesseract 'spa').
Degrada con elegancia: usa lo que esté instalado e informa lo que falta.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path


def rango_paginas(txt: str | None, total: int) -> list[int]:
    if not txt:
        return list(range(total))
    paginas: set[int] = set()
    for parte in txt.split(","):
        if "-" in parte:
            a, b = parte.split("-")
            paginas.update(range(int(a) - 1, min(int(b), total)))
        else:
            paginas.add(int(parte) - 1)
    return sorted(p for p in paginas if 0 <= p < total)


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto or "")
    return "\n".join(" ".join(l.split()) for l in texto.splitlines()).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--tablas", action="store_true")
    ap.add_argument("--paginas")
    ap.add_argument("--miniatura")
    ap.add_argument("--ocr", action="store_true")
    args = ap.parse_args()

    ruta = Path(args.pdf)
    datos = ruta.read_bytes()
    if not datos.startswith(b"%PDF-"):
        print("ERROR: el archivo no es un PDF válido (magic bytes).", file=sys.stderr)
        return 2

    res: dict = {
        "archivo": ruta.name,
        "tamano_bytes": len(datos),
        "sha256": hashlib.sha256(datos).hexdigest(),
        "avisos": [],
    }

    try:
        from pypdf import PdfReader
        lector = PdfReader(str(ruta))
        res["cifrado"] = lector.is_encrypted
        res["num_paginas"] = len(lector.pages)
        meta = lector.metadata or {}
        res["metadatos"] = {k.lstrip("/"): str(v) for k, v in meta.items()}
    except ImportError:
        res["avisos"].append("pypdf no instalado")
    except Exception as e:  # PDF dañado
        res["avisos"].append(f"pypdf no pudo leer: {e}")

    paginas_out = []
    try:
        import pdfplumber
        with pdfplumber.open(str(ruta)) as pdf:
            total = len(pdf.pages)
            res.setdefault("num_paginas", total)
            for i in rango_paginas(args.paginas, total):
                pag = pdf.pages[i]
                texto = normalizar(pag.extract_text() or "")
                info = {"pagina": i + 1, "ancho_pt": float(pag.width), "alto_pt": float(pag.height),
                        "caracteres": len(texto), "requiere_ocr": len(texto) < 20, "texto": texto}
                if args.tablas:
                    info["tablas"] = pag.extract_tables()
                paginas_out.append(info)
    except ImportError:
        res["avisos"].append("pdfplumber no instalado: pip install pdfplumber")

    if args.ocr and any(p["requiere_ocr"] for p in paginas_out):
        try:
            import pypdfium2 as pdfium
            import pytesseract
            doc = pdfium.PdfDocument(str(ruta))
            for p in paginas_out:
                if p["requiere_ocr"]:
                    img = doc[p["pagina"] - 1].render(scale=300 / 72).to_pil()
                    p["texto"] = normalizar(pytesseract.image_to_string(img, lang="spa"))
                    p["origen_texto"] = "ocr"
        except ImportError:
            res["avisos"].append("OCR no disponible: pip install pypdfium2 pytesseract + Tesseract")

    if args.miniatura:
        try:
            import pypdfium2 as pdfium
            doc = pdfium.PdfDocument(str(ruta))
            doc[0].render(scale=0.5).to_pil().save(args.miniatura)
            res["miniatura"] = args.miniatura
        except ImportError:
            res["avisos"].append("pypdfium2 no instalado: pip install pypdfium2")

    res["paginas"] = paginas_out

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"Archivo: {res['archivo']}  |  Páginas: {res.get('num_paginas')}  |  "
              f"{res['tamano_bytes']:,} bytes  |  SHA-256: {res['sha256'][:16]}…")
        for aviso in res["avisos"]:
            print(f"AVISO: {aviso}")
        for p in paginas_out:
            marca = "  [SIN TEXTO → posible escaneo, usar --ocr]" if p["requiere_ocr"] else ""
            print(f"\n===== Página {p['pagina']}{marca} =====\n{p['texto']}")
            for n, t in enumerate(p.get("tablas") or [], 1):
                print(f"\n--- Tabla {n} ---")
                for fila in t:
                    print(" | ".join("" if c is None else str(c) for c in fila))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
