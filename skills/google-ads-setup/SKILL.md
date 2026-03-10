# Google Ads MCP Setup

Diagnóstico y configuración del MCP `google-ads` para Claude Code y Claude Desktop.

## Cuándo usar esta skill

- Configurar el MCP por primera vez
- Problemas de conexión con el servidor
- Verificar que las credenciales funcionan

## Diagnóstico rápido

Intenta primero:
```
list_google_ads_accounts()
```

- **Funciona** → MCP configurado. Pregunta qué quiere hacer.
- **"tool not found"** → servidor MCP no registrado. Ver sección de configuración.
- **"authentication error"** → renovar credenciales Google.
- **"Config not found"** → falta `~/.google-ads-mcp/config.yaml`.

## Instalación

### Windows
```powershell
git clone https://github.com/gabogabucho/google-ads-mcp.git
cd google-ads-mcp
powershell -ExecutionPolicy Bypass -File install.ps1
```

### macOS / Linux
```bash
git clone https://github.com/gabogabucho/google-ads-mcp.git
cd google-ads-mcp
bash install.sh
```

## Configuración manual

### 1. Crear credenciales en Google Cloud Console
1. Ir a [console.cloud.google.com](https://console.cloud.google.com)
2. Habilitar: Google Ads API, Google Analytics Data API, Google Analytics Admin API
3. APIs & Services → Credentials → Create → OAuth 2.0 Client ID → Desktop app
4. Descargar JSON → guardar como `~/.google-ads-mcp/credentials.json`

### 2. Instalar dependencias
```bash
cd google-ads-mcp
uv sync
```

### 3. Crear config.yaml
Copiar `config/config.yaml.example` a `~/.google-ads-mcp/config.yaml` y rellenar.

### 4. Primera autenticación
```bash
# macOS/Linux
~/.local/share/google-ads-mcp/.venv/bin/python -m google_ads_mcp

# Windows
%USERPROFILE%\google-ads-mcp\.venv\Scripts\python.exe -m google_ads_mcp
```

### 5. Configurar Claude Desktop
Agregar a `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "google-ads": {
      "command": "RUTA_PYTHON_VENV",
      "args": ["-m", "google_ads_mcp"],
      "env": { "GOOGLE_ADS_MCP_CONFIG": "RUTA_CONFIG_YAML" }
    }
  }
}
```
El instalador muestra las rutas exactas al terminar.

### 6. Configurar Claude Code
```bash
claude mcp add google-ads \
  --env GOOGLE_ADS_MCP_CONFIG=$HOME/.google-ads-mcp/config.yaml \
  -- python -m google_ads_mcp
```

## Solución de problemas frecuentes

| Síntoma | Solución |
|---------|----------|
| `ModuleNotFoundError` | Usar ruta absoluta al Python del venv |
| `FileNotFoundError: credentials.json` | Verificar ruta en `google.credentials_path` |
| `Token expired` | Borrar `token.json` y re-autenticar |
| `Developer token not approved` | Solicitar aprobación en Google Ads → API Center |
| `Customer not found` | Verificar ID sin guiones (1234567890, no 123-456-7890) |

Ver `docs/troubleshooting.md` para más casos.
