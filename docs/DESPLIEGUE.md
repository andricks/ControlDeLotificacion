# Despliegue en Render

Arquitectura en producción (definida en `render.yaml`, raíz del repo):

```
Navegador ──https──▶ facturas-web (sitio estático, React)
                        ├─ /api/*  → reescritura (proxy) → facturas-api (FastAPI, uvicorn)
                        └─ /*      → index.html (SPA)            │
                                                                  ▼
                                                          MongoDB Atlas
```

El navegador solo ve el dominio del frontend. Por eso la cookie de sesión (`httpOnly`,
`SameSite=Strict`, `path=/api`) funciona sin CORS entre dominios y el frontend sigue llamando a
`/api/v1` igual que en desarrollo con el proxy de Vite.

## 0. Requisitos previos (una sola vez)

1. **Git**: instalar desde https://git-scm.com/download/win y reiniciar la terminal.
2. **Cuenta de GitHub** y un repositorio **privado** (el código contiene datos del negocio:
   cuentas bancarias, nombres).
3. **Rotar la contraseña del usuario de Atlas** (pendiente del ROADMAP: se compartió en el chat).
4. Comprobar localmente: `python .claude/scripts/validar.py` → todo OK.

## 1. Subir el código a GitHub

```powershell
cd "C:\Users\Andrick\Desktop\PROYECTO DE FACTURAS"
git init
git add .
git status          # REVISAR: no deben aparecer .env, documentos-muestra/, storage/, node_modules/, .venv/
git commit -m "Primera versión para despliegue"
git branch -M main
git remote add origin https://github.com/<usuario>/<repo>.git
git push -u origin main
```

## 2. MongoDB Atlas

1. **Database Access**: usuario solo para producción (rol *readWrite* sobre la base `facturas`),
   contraseña larga nueva.
2. **Network Access**: permitir las IP de salida de Render. En Render: servicio
   `facturas-api` → **Connect** → pestaña **Outbound** → copiar los rangos y agregarlos en Atlas.
   (Solo si no aparecen: `0.0.0.0/0`, que obliga a que la contraseña sea fuerte.)
3. Copiar la cadena `mongodb+srv://...` (Connect → Drivers → Python) con el usuario nuevo.

## 3. Crear los servicios en Render (Blueprint)

1. https://dashboard.render.com → **New** → **Blueprint** → conectar GitHub → elegir el repo.
2. Render lee `render.yaml` y propone `facturas-api` y `facturas-web`. Pide los valores `sync: false`:

| Variable | Valor |
|---|---|
| `MONGODB_URI` | cadena de Atlas del paso 2 |
| `GOOGLE_CLIENT_ID` | el mismo ID de cliente OAuth que usas en local |
| `ADMIN_CORREOS` | correos de Google administradores, separados por coma |
| `CORS_ORIGENES` | `https://facturas-web.onrender.com` (la URL real del frontend) |

`JWT_SECRETO` lo genera Render solo (`generateValue`); `ENTORNO=produccion` y
`COOKIE_SEGURA=true` ya vienen en el Blueprint.

3. **Apply**. El backend instala dependencias y **aplica las migraciones pendientes**
   (`python -m app.migrar` en el build) y luego arranca.

> **Si Render asignó otra URL** (p. ej. `facturas-api-x1y2.onrender.com` porque el nombre estaba
> ocupado): corregir `destination` de la regla `/api/*` en `render.yaml` y `CORS_ORIGENES`, hacer
> commit + push.

## 4. Google Cloud Console

APIs y servicios → Credenciales → tu **ID de cliente OAuth (Aplicación web)**:

- **Orígenes de JavaScript autorizados**: agregar `https://facturas-web.onrender.com`
  (dejar también los de localhost para desarrollo).
- **Pantalla de consentimiento**: si está en modo *Testing*, solo entran los "usuarios de prueba"
  listados; para uso real cambiar a **En producción** (los permisos básicos email/perfil no requieren
  verificación de Google).

Los cambios de Google pueden tardar unos minutos en aplicarse.

## 5. Verificación

1. `https://facturas-web.onrender.com/api/v1/salud` → `{"estado":"ok","base_datos":"conectada"}`.
2. Abrir `https://facturas-web.onrender.com` → **Iniciar sesión con Google** con un correo de
   `ADMIN_CORREOS`.
3. DevTools → Application → Cookies: existe `sesion` con *HttpOnly*, *Secure*, *SameSite=Strict*.
4. Crear/abrir una promesa y descargar su PDF; registrar un recibo y descargarlo.
5. `/docs` del backend debe dar 404 (en producción no se publica).

## 6. Uso diario

- **Actualizar**: `git push` a `main` → Render vuelve a construir y desplegar ambos servicios
  (con las migraciones nuevas).
- **Logs**: Render → servicio → *Logs*.
- **Revertir**: Render → servicio → *Events* → *Rollback* a un deploy anterior (las migraciones
  de datos no se revierten solas: usar `revertir` del script si hace falta).

## Notas y límites conocidos

- **Plan**: `facturas-api` usa `starter`. En `free` se duerme tras 15 min sin uso y la primera
  petición tarda ~1 min. El sitio estático es gratis.
- **Archivos (`STORAGE_DIR`)**: hoy no se guardan archivos en disco (los PDFs se generan en memoria),
  así que no hace falta disco persistente. Cuando exista la subida de archivos, agregar un *Disk*
  de Render al backend y apuntar `STORAGE_DIR` a su ruta de montaje.
- **Límite de intentos de inicio de sesión**: vive en la memoria del proceso; con una sola
  instancia es suficiente. La IP del cliente se toma de `X-Forwarded-For` (`--proxy-headers`).
- **Copias de seguridad**: dependen de Atlas (el plan M0 gratis no tiene backups automáticos).
