# Google Ads MCP Setup

Guía para verificar y configurar el servidor MCP de Google Ads (adloop) en Claude Desktop y Claude Code.

## Cuándo usar esta skill

Úsala cuando el usuario:
- Quiere configurar el MCP por primera vez
- Tiene problemas de conexión con el servidor
- Quiere verificar que todo esté correctamente instalado
- Necesita ayuda con las credenciales de Google

---

## Diagnóstico rápido

Primero, verifica si el MCP está conectado intentando:

```python
list_accounts()
```

**Si funciona:** el MCP está configurado correctamente. Pregunta qué quiere hacer con sus cuentas.

**Si falla con "tool not found":** el servidor MCP no está registrado. Sigue el flujo de instalación.

**Si falla con "authentication error":** las credenciales de Google necesitan renovarse.

**Si falla con "config not found":** falta el archivo `~/.adloop/config.yaml`.

---

## Flujo de instalación paso a paso

### 1. Verificar Python y uv

```bash
python --version  # Debe ser 3.11+
uv --version      # Gestor de paquetes
```

Si no tiene uv instalado:
- **Mac/Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows:** `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

### 2. Clonar e instalar AdLoop

```bash
git clone https://github.com/kLOsk/adloop.git ~/adloop
cd ~/adloop
uv sync
```

Verificar instalación:
```bash
~/adloop/.venv/bin/python -m adloop --help
```

### 3. Crear configuración de Google Cloud

Guía al usuario por estos pasos:

**a) Google Cloud Console:**
1. `console.cloud.google.com` → crear proyecto nuevo
2. "APIs & Services" → "Enable APIs" → buscar y habilitar:
   - "Google Ads API"
   - "Google Analytics Data API"
   - "Google Analytics Admin API"

**b) Credenciales OAuth:**
1. "APIs & Services" → "Credentials" → "+ Create Credentials" → "OAuth 2.0 Client ID"
2. Application type: **Desktop app**
3. Descargar JSON → guardar como `~/.adloop/credentials.json`

**c) Developer Token de Google Ads:**
1. `ads.google.com` → cuenta → herramienta (llave inglesa) → "API Center"
2. Si no existe, solicitar acceso (puede tardar días)
3. Para pruebas: usar token de nivel TEST (sin cambios reales)

### 4. Crear config.yaml

```bash
mkdir -p ~/.adloop
```

Crear `~/.adloop/config.yaml` con los valores del usuario:

```yaml
google:
  project_id: "tu-gcp-project-id"
  credentials_path: "~/.adloop/credentials.json"
  token_path: "~/.adloop/token.json"

ga4:
  property_id: "123456789"

ads:
  developer_token: "ABcDEfGHiJkLmNoPQRsTuVwX"
  customer_id: "1234567890"
  login_customer_id: "1234567890"  # MCC si aplica

safety:
  max_daily_budget: 100.0
  max_bid_increase_pct: 50
  require_dry_run: true
  log_file: "~/.adloop/audit.log"
```

**Importante:** `customer_id` sin guiones (1234567890, no 123-456-7890)

### 5. Primera autenticación

```bash
~/adloop/.venv/bin/python -m adloop
```

Se abrirá el navegador. Autenticar con la cuenta Google que tiene acceso a Google Ads. Esto guarda `~/.adloop/token.json`.

### 6. Configurar en Claude Desktop

Editar el archivo de configuración de Claude Desktop:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "C:/Users/USUARIO/adloop/.venv/Scripts/python.exe",
      "args": ["-m", "adloop"],
      "env": {
        "ADLOOP_CONFIG": "C:/Users/USUARIO/.adloop/config.yaml"
      }
    }
  }
}
```

**Mac/Linux:**
```json
{
  "mcpServers": {
    "google-ads": {
      "command": "/Users/USUARIO/adloop/.venv/bin/python",
      "args": ["-m", "adloop"],
      "env": {
        "ADLOOP_CONFIG": "/Users/USUARIO/.adloop/config.yaml"
      }
    }
  }
}
```

Reiniciar Claude Desktop completamente.

### 7. Configurar en Claude Code

Opción A - Via CLI (recomendado):
```bash
claude mcp add google-ads \
  --env ADLOOP_CONFIG=$HOME/.adloop/config.yaml \
  -- python -m adloop
```

Opción B - Archivo `.mcp.json` en el proyecto:
```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python",
      "args": ["-m", "adloop"],
      "cwd": "/ruta/a/adloop",
      "env": {
        "ADLOOP_CONFIG": "/ruta/a/.adloop/config.yaml"
      }
    }
  }
}
```

### 8. Instalar Skills en Claude Code

```bash
SKILLS_DIR=~/.claude/skills
mkdir -p $SKILLS_DIR

# Desde el directorio del proyecto google-ads-mcp
cp -r skills/google-ads-analyze $SKILLS_DIR/
cp -r skills/google-ads-manage $SKILLS_DIR/
cp -r skills/google-ads-ga4 $SKILLS_DIR/
cp -r skills/google-ads-setup $SKILLS_DIR/
```

---

## Verificación final

Una vez configurado, prueba cada skill:

```
/google-ads-setup   → este diagnóstico
/google-ads-analyze → pide rendimiento de campañas
/google-ads-ga4     → pide usuarios activos en tiempo real
/google-ads-manage  → pide pausar una campaña (solo draft, no confirmes)
```

Si `list_accounts()` devuelve cuentas, ¡todo está funcionando!

---

## Solución de problemas comunes

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `ModuleNotFoundError: adloop` | Virtualenv no activo o adloop no instalado | Verificar ruta de Python en config |
| `FileNotFoundError: credentials.json` | Ruta incorrecta en config.yaml | Verificar que `credentials_path` apunte al archivo |
| `Token expired` | Token de OAuth vencido | Borrar `token.json` y re-autenticar |
| `Access denied: Developer Token` | Token en nivel TEST | Solicitar acceso a producción en Google Ads |
| `Customer not found` | customer_id incorrecto | Verificar ID sin guiones en Google Ads dashboard |
| `MCP server not responding` | Ruta de Python incorrecta | Usar ruta absoluta al .venv/bin/python |

---

## Seguridad

- **Nunca** compartas `credentials.json`, `token.json` ni `config.yaml` en Git
- Agrega estos archivos a `.gitignore`
- Los archivos en `~/.adloop/` contienen credenciales sensibles
- El `developer_token` da acceso a toda la API de Google Ads — trátalo como una contraseña
