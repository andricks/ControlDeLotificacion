---
paths:
  - "frontend/**/*.ts"
  - "frontend/**/*.tsx"
  - "frontend/**/*.css"
---

# Reglas: frontend

- TypeScript `strict`; prohibido `any` (usar `unknown` + Zod).
- Datos del servidor con TanStack Query (hooks en `features/<dominio>/hooks.ts`); no copiarlos a `useState`.
- Formularios: React Hook Form + `zodResolver`; esquemas en `features/<dominio>/esquemas.ts`; mensajes en español.
- Cada vista de datos implementa estados cargando / vacío / error.
- Usar componentes de `components/ui/` antes de crear nuevos; colores solo con tokens de Tailwind (`primario`, `acento`, `alerta`, `peligro`), sin hex sueltos.
- Montos llegan como string: mostrarlos con `lib/formato.ts`; no hacer cálculos de negocio en el cliente (solo vista previa).
- Accesibilidad: `label` en cada campo, foco visible, teclado, `aria-*` en iconos sin texto.
- Descargas vía `lib/descargas.ts` (blob + nombre desde `Content-Disposition`), con estado de carga en el botón.
- Sin `console.log` ni `dangerouslySetInnerHTML`.
