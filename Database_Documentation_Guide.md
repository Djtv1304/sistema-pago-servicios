# Documentación técnica de CooperativaDB — Cómo actualizar y desplegar

Este documento explica cómo funciona el pipeline de documentación de la base de
datos (tablas, columnas, relaciones y diagrama ER interactivo) y qué pasos
seguir cada vez que el esquema cambia. Pensado para que cualquier dev del
equipo pueda reproducirlo sin tener que redescubrir nada.

## 1. Qué genera este pipeline

- **`docs/schema/`** — documentación en Markdown (una página por tabla, con su
  descripción, columnas, índices y relaciones) más diagramas ER en SVG.
  Se ve directamente en GitHub sin nada extra, porque GitHub renderiza `.md`
  automáticamente.
- **`dist/`** — un sitio estático (HTML/JS/CSS) con el diagrama ER
  **interactivo** de Liam ERD. Es lo que se publica en Cloudflare.

Fuente de verdad: la base **CooperativaDB** en Azure SQL. Todo lo de arriba se
regenera a partir de ella, nunca se edita a mano.

## 2. Herramientas que hay que tener instaladas

| Herramienta | Para qué | Cómo se instala |
|---|---|---|
| Git | Subir cambios al repo | `winget install --id Git.Git -e` |
| Node.js LTS | Correr Liam ERD vía `npx` | `winget install OpenJS.NodeJS.LTS` |
| tbls | Introspeccionar la base y generar la doc | Descargar el `.zip` de [github.com/k1LoW/tbls/releases](https://github.com/k1LoW/tbls/releases), extraer `tbls.exe` y agregarlo al PATH |

Verificar con: `tbls version`, `node -v`, `git --version`.

## 3. Acceso a la base

1. La IP de quien va a correr esto tiene que estar habilitada en el firewall
   del servidor Azure SQL (**Azure Portal → tu SQL Server → Seguridad de red →
   Firewall**). Sin esto, la conexión da timeout.
2. Cargar la cadena de conexión como variable de entorno. Por convención,
   en este proyecto se usa el nombre `COOP_DSN`:

   ```powershell
   $env:COOP_DSN = "sqlserver://usuario:password@servidor.database.windows.net:1433/CooperativaDB?encrypt=true"
   ```

   Si la contraseña tiene caracteres como `#`, `@` o `%`, tienen que ir
   URL-encodeados dentro de la cadena.

## 4. Flujo para actualizar la documentación

Correr todo esto desde la raíz del proyecto, en la terminal (PowerShell,
puede ser la integrada de PyCharm con `Alt+F12`):

```powershell
# 1. Generar la documentación en Markdown + SVG (usa .tbls.yml)
tbls doc --config .tbls.yml

# 2. Exportar el schema completo a JSON (para alimentar a Liam ERD)
tbls out -t json --config .tbls.yml docs/schema/schema.json

# 3. Reconstruir el diagrama interactivo
# Antes de correr esto, borrar manualmente la carpeta "dist" del proyecto
# (por ejemplo desde el explorador de archivos o el panel de PyCharm), para
# no mezclar assets viejos con los nuevos.
npx @liam-hq/cli erd build --format tbls --input docs/schema/schema.json

# 4. Revisar localmente antes de publicar (opcional pero recomendado)
npx serve dist

# 5. Subir los cambios — esto dispara el redeploy automático en Cloudflare
git add docs dist .tbls.yml
git commit -m "Actualiza documentacion del esquema"
git push
```

El deploy a Cloudflare se hace por separado, desde la cuenta correspondiente,
una vez que los cambios ya están en el repo.

## 5. Cuándo tocar `.tbls.yml`

- **Se agrega una tabla nueva**: sumar su entrada en la sección `comments:`
  (con `tableComment` y `columnComments`) y agregarla al `viewpoints:` del
  dominio de negocio que corresponda (Catalogo, Clientes, Core, Boveda, Caja,
  Contabilidad, Credito, Organizacion).
- **Los nombres de tabla siempre llevan el prefijo de schema**: como
  CooperativaDB está segmentada en schemas (`Catalogo`, `Clientes`, `Core`,
  `Boveda`, `Caja`, `Contabilidad`, `Credito`, `Organizacion`), toda entrada
  de `comments:` o `viewpoints:` debe escribirse como `Schema.Tabla` (ej.
  `Credito.GaranteBien`), nunca solo `Tabla`.

## 6. Troubleshooting rápido

| Síntoma | Causa probable | Solución |
|---|---|---|
| Se genera `dbdoc/` en vez de `docs/schema/` | tbls no cargó `.tbls.yml` | Correr con `--config .tbls.yml` explícito |
| `failed to add table comment: not found table 'X'` | Falta el prefijo de schema en `comments:`/`viewpoints:` | Usar `Schema.Tabla` en vez de `Tabla` |
| El diagrama de Liam no muestra cambios recientes | `dist/` o el navegador tienen cache viejo | Borrar `dist/`, regenerar, y hacer hard refresh (`Ctrl+Shift+R`) |
| Conexión a Azure SQL da timeout | IP no habilitada en el firewall | Agregar la IP actual en Azure Portal → SQL Server → Firewall |
| Login a Azure SQL falla | Formato de usuario | Probar `usuario@nombre-servidor` en vez de solo `usuario` |
