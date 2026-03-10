# google-ads-mcp

Servidor MCP (Model Context Protocol) para gestionar Google Ads y Google Analytics 4 directamente desde **Claude Code** y **Claude Desktop**.

> Escrito por [Gabriel Urrutia](https://x.com/gabogabucho).
> Inspirado en [AdLoop](https://github.com/kLOsk/adloop) por kLOsk — reimplementación independiente optimizada para Claude con soporte nativo en Windows, macOS y Linux.

---

## ¿Qué hace?

- Analizar rendimiento de campañas, anuncios y keywords
- Consultar términos de búsqueda y proponer negativos
- Pausar / activar campañas, grupos y anuncios
- Crear anuncios de búsqueda responsivos (RSA)
- Agregar negative keywords
- Ejecutar queries GAQL personalizadas
- Consultar reportes y usuarios en tiempo real de GA4

Todo con un sistema de seguridad **preview → confirm**: ningún cambio se aplica sin aprobación explícita.

---

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes)
- Cuenta de Google Ads con acceso a la API
- Google Cloud Project con las APIs habilitadas

---

## Instalación

### Windows (PowerShell)

```powershell
git clone https://github.com/gabogabucho/google-ads-mcp.git
cd google-ads-mcp
powershell -ExecutionPolicy Bypass -File install.ps1
```

### macOS / Linux (bash)

```bash
git clone https://github.com/gabogabucho/google-ads-mcp.git
cd google-ads-mcp
bash install.sh
```

Los instaladores:
1. Verifican Python, uv y git
2. Crean el virtualenv e instalan dependencias
3. Crean `~/.google-ads-mcp/config.yaml` desde el ejemplo
4. Copian las Skills a `~/.claude/skills/`
5. Muestran el snippet exacto para configurar Claude Desktop

---

## Configuración de Google

### 1. Google Cloud Project
1. Ve a [console.cloud.google.com](https://console.cloud.google.com) → crea un proyecto
2. Habilita estas APIs:
   - **Google Ads API**
   - **Google Analytics Data API**
   - **Google Analytics Admin API**

### 2. Credenciales OAuth 2.0
1. APIs & Services → Credentials → Create → **OAuth 2.0 Client ID**
2. Application type: **Desktop app**
3. Descarga el JSON → guárdalo como `~/.google-ads-mcp/credentials.json`

### 3. Developer Token de Google Ads
- En Google Ads: herramienta (llave inglesa) → **API Center** → copia el token
- El token de nivel **TEST** solo funciona con cuentas de prueba

### 4. Editar config.yaml
```bash
# macOS/Linux
$EDITOR ~/.google-ads-mcp/config.yaml

# Windows
notepad %USERPROFILE%\.google-ads-mcp\config.yaml
```

Ver `config/config.yaml.example` para todos los campos.

### 5. Primera autenticación

El primer `python -m google_ads_mcp` abre el navegador para autenticar con Google.
El token se guarda en `~/.google-ads-mcp/token.json` y se renueva automáticamente.

---

## Configurar en Claude Desktop

Edita `claude_desktop_config.json`:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "RUTA_AL_PYTHON_DEL_VENV",
      "args": ["-m", "google_ads_mcp"],
      "env": {
        "GOOGLE_ADS_MCP_CONFIG": "RUTA_A_CONFIG_YAML"
      }
    }
  }
}
```

El instalador muestra las rutas exactas para tu sistema al terminar.

---

## Configurar en Claude Code

```bash
# Añadir globalmente
claude mcp add google-ads \
  --env GOOGLE_ADS_MCP_CONFIG=$HOME/.google-ads-mcp/config.yaml \
  -- python -m google_ads_mcp
```

O crea `.mcp.json` en la raíz del proyecto (ver `config/mcp.json.example`).

---

## Skills disponibles

Después de instalar, usa estos comandos en Claude Code:

| Comando | Descripción |
|---------|-------------|
| `/google-ads-setup` | Diagnóstico de configuración y guía de setup |
| `/google-ads-analyze` | Analizar campañas, keywords y search terms |
| `/google-ads-manage` | Gestionar campañas con safety checks |
| `/google-ads-ga4` | Reportes y tiempo real de GA4 |

---

## Herramientas MCP

### Lectura — Google Ads
| Tool | Descripción |
|------|-------------|
| `list_google_ads_accounts` | Todas las cuentas accesibles |
| `get_campaign_performance` | Métricas de campañas |
| `get_ad_performance` | Métricas de anuncios |
| `get_keyword_performance` | Keywords con Quality Score |
| `get_search_terms` | Términos de búsqueda reales |
| `run_gaql_query` | Query GAQL personalizada |

### Lectura — GA4
| Tool | Descripción |
|------|-------------|
| `list_ga4_properties` | Cuentas y propiedades GA4 |
| `run_ga4_report` | Reporte personalizado |
| `get_realtime_users` | Usuarios activos ahora |
| `get_ga4_events` | Eventos configurados (30 días) |

### Escritura (preview → confirm)
| Tool | Descripción |
|------|-------------|
| `preview_campaign_status_change` | Vista previa: pausar/activar/eliminar campaña |
| `preview_add_negative_keywords` | Vista previa: agregar negative keywords |
| `preview_responsive_search_ad` | Vista previa: crear anuncio RSA |
| `apply_change` | Aplicar cambio por plan_id (dry_run=True por defecto) |

---

## Sistema de seguridad

```
Usuario pide cambio
    ↓
preview_*()  →  valida límites, genera plan con ID corto
    ↓
Claude muestra preview, pide confirmación
    ↓
apply_change(plan_id, dry_run=True)   ← simulación primero
    ↓
apply_change(plan_id, dry_run=False)  ← solo con OK explícito del usuario
```

**Protecciones activas:**
- Cap de presupuesto diario máximo (configurable)
- Límite de % de aumento de bids
- Operaciones bloqueadas por lista
- Log de auditoría en `~/.google-ads-mcp/audit.log`
- RSAs nuevos creados en estado **PAUSED**

---

## Estructura del proyecto

```
google-ads-mcp/
├── src/google_ads_mcp/
│   ├── server.py       # FastMCP: definición de todas las tools
│   ├── ads.py          # Google Ads API (lectura y escritura)
│   ├── ga4.py          # Google Analytics 4 API (solo lectura)
│   ├── auth.py         # OAuth 2.0 con token caching
│   ├── config.py       # Carga de config.yaml
│   └── safety.py       # Guards, plan store, audit log
├── skills/
│   ├── google-ads-analyze/SKILL.md
│   ├── google-ads-manage/SKILL.md
│   ├── google-ads-ga4/SKILL.md
│   └── google-ads-setup/SKILL.md
├── config/
│   ├── config.yaml.example
│   ├── claude-desktop-config.json.example
│   └── mcp.json.example
├── docs/troubleshooting.md
├── install.sh          # macOS / Linux
├── install.ps1         # Windows PowerShell
├── pyproject.toml
└── LICENSE             # MIT
```

---

## Créditos

- **Gabriel Urrutia** ([@gabogabucho](https://x.com/gabogabucho)) — autor
- Inspirado en [AdLoop](https://github.com/kLOsk/adloop) por [kLOsk](https://github.com/kLOsk)

MIT License — ver [LICENSE](LICENSE).
