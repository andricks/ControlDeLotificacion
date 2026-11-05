---
name: diseno-frontend
description: Diseño e implementación del frontend con React + TypeScript + Vite + Tailwind — sistema de diseño, layout de la app, tablas con filtros, formularios con validación, visor de PDF, subida de archivos, botones de descarga, accesibilidad y estados de carga/error. Usar al crear pantallas, componentes o flujos de usuario en frontend/.
---

# Diseño de frontend

## Estructura

```
frontend/src/
  api/            cliente.ts (axios/fetch + token + manejo 401), tipos.ts, facturas.ts, contratos.ts...
  components/ui/  Boton, Campo, Select, Tabla, Paginacion, Modal, Toast, Badge, ZonaSubida, VisorPdf, Vacio
  components/layout/  Layout (sidebar + header), RutaProtegida
  features/
    facturas/     ListaFacturas.tsx, FormFactura.tsx, DetalleFactura.tsx, esquemas.ts (Zod), hooks.ts (TanStack Query)
    contratos/  planos/  terrenos/  partes/  dashboard/
  lib/            formato.ts (moneda Q, fechas dd/mm/aaaa), descargas.ts
  pages/          Login, NoEncontrado
```

Estado del servidor → **TanStack Query** (nunca duplicar en useState). Estado de formulario → **React Hook Form + zodResolver**. Estado global mínimo (usuario/sesión) → Context.

## Sistema de diseño

Aplicación de oficina/administrativa: sobria, densa en información, legible.

- **Colores (tokens Tailwind en `tailwind.config`):**
  - `primario` azul institucional `#1e3a5f` (acciones principales, sidebar)
  - `acento` `#2f855a` (éxito, "pagada", "vigente")
  - `alerta` `#b7791f` (por vencer, borrador) · `peligro` `#c53030` (anulada, vencido, eliminar)
  - Neutros slate para fondos y bordes. Contraste mínimo WCAG AA (4.5:1 en texto).
- **Tipografía:** Inter / system-ui; 14px base en tablas, 16px en formularios; números con `tabular-nums` y alineados a la derecha.
- **Espaciado:** escala de 4px; tarjetas `rounded-lg border shadow-sm`; máx. ancho de formularios ~720px.
- **Estados por color + texto** (nunca solo color): `<Badge tono="peligro">Anulada</Badge>`.
- **Iconos:** lucide-react, siempre con `aria-label` o texto acompañante.

## Layout

- Sidebar: Dashboard · Facturas · Contratos · Planos · Terrenos · Clientes/Partes · Reportes · (Admin) Usuarios · Auditoría.
- Header: buscador global (busca en número, NIT, nombre, finca y texto de PDFs), usuario, cerrar sesión.
- Responsive: sidebar colapsable < 1024px; tablas con scroll horizontal en móvil.

## Patrones de pantalla

**Lista** (todas las entidades): barra de filtros (búsqueda con debounce 300ms, rango de fechas, estado) sincronizada con la URL (`useSearchParams`) → tabla paginada con ordenamiento → acciones por fila (ver, editar, descargar PDF) → selección múltiple para **"Descargar seleccionados (ZIP)"**.

**Formulario**: secciones con títulos; validación en vivo tras el primer submit; errores del backend mapeados a campos; botón guardar deshabilitado mientras envía; confirmación al salir con cambios sin guardar. Factura: tabla editable de líneas con cálculo en vivo de subtotal/IVA/total (solo visual — el backend recalcula).

**Detalle / expediente**: cabecera con datos clave + estado; pestañas "Datos · Documentos adjuntos · Relacionados · Historial"; visor PDF embebido; botones "Descargar PDF" y "Descargar expediente completo".

**Subida de archivos** (`ZonaSubida`): drag & drop + botón; valida tipo/tamaño en cliente (el servidor valida de nuevo); barra de progreso; tras subir, muestra datos extraídos del PDF como **sugerencias** a confirmar.

## Estados obligatorios en cada vista de datos

`cargando` (skeleton, no spinner a pantalla completa) · `vacío` (mensaje + acción "Crear primera factura") · `error` (mensaje + "Reintentar") · `éxito`.

## Accesibilidad

- Todo campo con `<label>`; errores con `aria-describedby`; foco visible; navegación completa con teclado; modales con trampa de foco y cierre con Esc.
- `lang="es"` en `index.html`.

## Formatos (lib/formato.ts)

```ts
export const moneda = (v: number | string, m = "GTQ") =>
  new Intl.NumberFormat("es-GT", { style: "currency", currency: m }).format(Number(v));
export const fecha = (iso: string) =>
  new Intl.DateTimeFormat("es-GT", { timeZone: "America/Guatemala" }).format(new Date(iso));
```
Los montos llegan del backend como **string** (Decimal serializado) — no hacer aritmética de negocio con ellos en el cliente.

## Validación visual

Tras cambios de UI, levantar `npm run dev` y comprobar la pantalla (skill `run` o navegador). Revisar: estados vacío/error, textos largos, móvil (≈400px), modo teclado.
