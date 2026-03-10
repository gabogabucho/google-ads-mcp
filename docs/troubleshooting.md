# Troubleshooting

---

## TypeError: FastMCP() got unexpected keyword argument 'description'

**Síntoma:**
```
TypeError: FastMCP() got unexpected keyword argument(s): 'description'
```
al ejecutar `python -m google_ads_mcp` o al iniciar Claude Desktop con el MCP configurado.

**Causa:** fastmcp 3.x eliminó los parámetros `description` y `dependencies` del constructor `FastMCP()`.

**Fix:** Ya corregido en el repositorio. Si tenés un clone anterior al fix, editá `src/google_ads_mcp/server.py` y reemplazá la inicialización:

```python
# ANTES (roto con fastmcp >= 3.0)
mcp = FastMCP(
    "google-ads-mcp",
    description="MCP server for Google Ads and GA4",
    dependencies=["google-ads"],
)

# DESPUÉS
mcp = FastMCP("google-ads-mcp")
```

Luego reinstalá las dependencias:
```powershell
# Windows
uv pip install -e .

# macOS / Linux
uv pip install -e .
```

**Verificación:** ejecutar manualmente el servidor debe mostrar el banner de FastMCP y terminar con `EOF while parsing a value` (normal — espera JSON-RPC de Claude, no una terminal):
```
╭─────────────────────────────────────────────╮
│            FastMCP 3.x.x                    │
│  🖥  Server: google-ads-mcp                 │
╰─────────────────────────────────────────────╯
```

---

## El MCP no aparece en Claude

**Síntoma:** Las herramientas `list_google_ads_accounts`, `get_campaign_performance`, etc. no están disponibles.

**Soluciones:**
1. Verificar que la ruta de Python en la config apunta al **virtualenv del proyecto**, no al Python del sistema
2. Reiniciar Claude Desktop completamente (cerrar también desde la bandeja del sistema)
3. En Claude Code: ejecutar `claude mcp list` para ver si aparece "google-ads"
4. Revisar logs: en Claude Desktop, menú Developer → Show Logs

---

## Error: `ModuleNotFoundError: No module named 'google_ads_mcp'`

El servidor MCP no encuentra el paquete. Causa: la ruta de Python en la configuración apunta al Python del sistema, no al virtualenv del proyecto.

**Fix:** Usá la ruta absoluta al Python del virtualenv:
- **macOS/Linux:** `/ruta/al/proyecto/google-ads-mcp/.venv/bin/python`
- **Windows:** `C:\ruta\al\proyecto\google-ads-mcp\.venv\Scripts\python.exe`

Verificá con:
```bash
# macOS/Linux
/ruta/al/proyecto/google-ads-mcp/.venv/bin/python -c "import google_ads_mcp; print('OK')"

# Windows PowerShell
C:\ruta\al\proyecto\google-ads-mcp\.venv\Scripts\python.exe -c "import google_ads_mcp; print('OK')"
```

---

## Error: `FileNotFoundError: ~/.google-ads-mcp/credentials.json`

El archivo de credenciales OAuth no existe en la ruta configurada.

**Fix:**
1. Descargá el JSON desde Google Cloud Console (APIs & Services → Credentials)
2. Guardalo exactamente en la ruta especificada en `config.yaml` bajo `google.credentials_path`
3. Por defecto: `~/.google-ads-mcp/credentials.json`

---

## Error: `Token has been expired or revoked`

El token de OAuth expiró o fue revocado.

**Fix:**
```bash
# macOS/Linux
rm ~/.google-ads-mcp/token.json

# Windows PowerShell
Remove-Item $env:USERPROFILE\.google-ads-mcp\token.json
```

Luego volvé a ejecutar el servidor manualmente para re-autenticar (se abre el navegador):
```powershell
# Windows
C:\ruta\al\proyecto\.venv\Scripts\python.exe -m google_ads_mcp
```

---

## Error: `Access denied: Developer token has not been approved`

El Developer Token está en nivel **TEST** y no puede acceder a cuentas de producción.

**Opciones:**
1. **Para pruebas:** usá una cuenta de prueba de Google Ads (test account) con el token TEST — ver sección "Cuenta Manager y tester" más abajo
2. **Para producción:** solicitá la aprobación del token en Google Ads → Tools → API Center

El proceso de aprobación puede tomar varios días.

---

## Error: `Customer ID not found` o `Invalid customer ID`

**Causas posibles:**
1. El ID tiene guiones (`123-456-7890`) cuando debería ser solo números (`1234567890`)
2. La cuenta no es accesible con las credenciales actuales
3. El `login_customer_id` (MCC) no tiene acceso a ese `customer_id`

**Fix:** usá `list_google_ads_accounts` para ver las cuentas accesibles y sus IDs exactos.

---

## Error de límites de seguridad (`Budget cap exceeded`)

El cambio propuesto supera el `max_daily_budget_usd` configurado en `config.yaml`.

**Fix:** Editá `~/.google-ads-mcp/config.yaml` y aumentá `safety.max_daily_budget_usd`. Luego reiniciá el servidor MCP (reiniciá Claude Desktop).

---

## El servidor MCP se desconecta frecuentemente

**Causas posibles:**
1. El proceso Python se cae por un error interno
2. El token de Google expiró y el servidor no lo maneja correctamente

**Solución temporal:** Reiniciar Claude Desktop regenera la conexión MCP.

**Solución permanente:** Revisar logs del servidor. En Claude Desktop: Developer → MCP Logs.

---

## Las skills `/google-ads-*` no aparecen en Claude Code

Las skills deben estar en `~/.claude/skills/`:

```bash
ls ~/.claude/skills/
# Debe mostrar: google-ads-analyze  google-ads-manage  google-ads-ga4  google-ads-setup
```

Si no están, el instalador las copia automáticamente. También podés hacerlo manualmente:
```bash
# macOS/Linux
cp -r /ruta/a/google-ads-mcp/skills/google-ads-* ~/.claude/skills/

# Windows PowerShell
Copy-Item -Recurse C:\ruta\al\proyecto\skills\google-ads-* $env:USERPROFILE\.claude\skills\
```

---

## Datos de GA4 no coinciden con Google Ads

Es normal una discrepancia del 5–15% entre los datos de GA4 y Google Ads por:
- Diferencia de atribución (last-click vs data-driven)
- Filtros de bots y spam en GA4
- Usuarios con cookies bloqueadas

Para análisis precisos, definí un modelo de atribución común y comparar tendencias, no números absolutos.

---

## Comandos útiles de diagnóstico

```powershell
# Windows PowerShell

# Verificar instalación de uv
uv --version

# Listar paquetes instalados en el venv
uv pip list

# Ver versión de fastmcp instalada
uv pip show fastmcp

# Reinstalar dependencias
uv pip install -e .

# Ejecutar el servidor MCP manualmente (solo para testing)
# El error EOF al final es NORMAL — espera JSON-RPC de Claude Desktop
.\.venv\Scripts\python.exe -m google_ads_mcp
```

```bash
# macOS / Linux

uv --version
uv pip list
uv pip show fastmcp
uv pip install -e .
.venv/bin/python -m google_ads_mcp
```

---

## Cuenta Manager de Google Ads y usuario tester

Para usar la API de Google Ads con Developer Token en nivel **TEST** necesitás:
1. Una cuenta **Manager (MCC)** — donde obtener el Developer Token
2. Una **cuenta de prueba (test account)** vinculada a esa MCC

### Paso 1 — Crear una cuenta Manager (MCC)

1. Andá a [ads.google.com](https://ads.google.com)
2. Si ya tenés una cuenta normal, hace falta crear una separada. Usá una cuenta de Google distinta o navegación de incógnito
3. Al crear la cuenta, elegí **"Crear una cuenta de administrador"** (no una cuenta normal)
4. Completá el formulario sin agregar métodos de pago — las cuentas manager no gastan dinero
5. Una vez creada, accedé a **Herramientas (llave inglesa) → API Center**
6. Copiá tu **Developer Token** — al inicio estará en nivel TEST

### Paso 2 — Crear una cuenta de prueba (test account)

Las cuentas de prueba solo son visibles desde la MCC donde se crean.

1. Desde tu MCC, andá a **Cuentas → Todas las cuentas → Crear cuenta**
2. En el formulario, marcá **"Esta es una cuenta de prueba"**
3. Completá nombre y zona horaria
4. La cuenta creada aparece con una etiqueta "TEST" en el listado

### Paso 3 — Obtener el Customer ID de la cuenta de prueba

1. En tu MCC, hacé clic en la cuenta de prueba recién creada
2. El ID aparece en la URL o en la esquina superior: formato `123-456-7890`
3. Quitale los guiones para usarlo en `config.yaml`: `customer_id: "1234567890"`

### Paso 4 — Configurar config.yaml con la MCC y la cuenta de prueba

```yaml
ads:
  developer_token: "tu-developer-token-de-la-mcc"
  customer_id: "ID-de-la-cuenta-de-prueba-sin-guiones"
  login_customer_id: "ID-de-la-MCC-sin-guiones"  # importante: este es el MCC
```

### Paso 5 — Agregar un usuario tester (opcional)

Para dar acceso a otra persona a tu cuenta de prueba sin compartir credenciales:

1. En Google Ads, andá a **Herramientas → Acceso y seguridad → Usuarios**
2. Hacé clic en el **+** para agregar usuario
3. Ingresá el email de Google del usuario
4. Asigná el nivel de acceso: **Administrador** para acceso completo, **Estándar** para la mayoría de las operaciones
5. El usuario recibirá un email de invitación

> **Nota:** El Developer Token en nivel TEST solo funciona con cuentas de prueba. Para acceder a cuentas de producción con dinero real, necesitás solicitar la aprobación del token en API Center (proceso de revisión de Google, puede tomar varios días).
