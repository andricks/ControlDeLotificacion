# ADR-001: Stack tecnológico

- **Estado:** Aceptado parcialmente — **base de datos y ORM reemplazados por ADR-002 (MongoDB Atlas + Beanie)**
- **Fecha:** 2026-09-29

## Contexto

Sistema web para registrar facturas, contratos y planos de terrenos, con fuerte necesidad de **leer PDFs** (extraer datos) y **generar PDFs** (descargas, expedientes, reportes). Desarrollo en Windows con Python 3.13 y Node disponibles.

## Decisión

| Área | Elección | Alternativas descartadas |
|---|---|---|
| Backend | **FastAPI** (Python) | Django (más pesado para una API SPA), Node/Nest (ecosistema PDF más débil) |
| ORM / migraciones | **SQLAlchemy 2.0 + Alembic** | Django ORM, Prisma |
| BD | **PostgreSQL 16** | MySQL (peor búsqueda de texto completo en español), SQLite (concurrencia) |
| Leer PDF | **pdfplumber + pypdf + pypdfium2**, OCR **pytesseract** | PyMuPDF (licencia AGPL) |
| Generar PDF | **ReportLab** | WeasyPrint (dependencias GTK difíciles en Windows), wkhtmltopdf (abandonado) |
| Frontend | **React + Vite + TypeScript + Tailwind** | Angular, Vue (válidos; se elige por ecosistema y empleabilidad) |
| Datos/forms | **TanStack Query, React Hook Form + Zod** | Redux (innecesario) |
| Calidad | ruff, pytest, ESLint, Prettier, Vitest | — |

## Consecuencias

- Python concentra todo lo relacionado con PDF (una sola fuente de verdad).
- Dos lenguajes (Python + TS): mayor superficie, pero separación clara API/UI.
- Si en el futuro se necesitan plantillas HTML→PDF muy elaboradas, evaluar WeasyPrint en Docker (nuevo ADR).
