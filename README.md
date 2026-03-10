# Google Ads MCP para Claude

Integración de Google Ads y GA4 directamente en Claude Desktop y Claude Code, basada en [AdLoop](https://github.com/kLOsk/adloop).

## ¿Qué hace esto?

Un servidor MCP (Model Context Protocol) que expone herramientas de Google Ads y Google Analytics 4 a Claude, permitiéndote:

- Analizar rendimiento de campañas, anuncios y keywords
- Consultar términos de búsqueda y proponer negativos
- Pausar/activar campañas, grupos y anuncios
- Crear anuncios de búsqueda responsivos (RSA)
- Agregar keywords y negative keywords
- Ejecutar queries GAQL personalizadas
- Consultar datos de GA4

Todo con un sistema de seguridad de 3 pasos: **draft → preview → confirm**.

---

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (gestor de paquetes Python)
- Cuenta de Google Ads con acceso API
- Google Cloud Project con las APIs habilitadas

---

## Instalación rápida

### 1. Clonar AdLoop

```bash
git clone https://github.com/kLOsk/adloop.git ~/adloop
cd ~/adloop
uv sync
```

### 2. Configurar credenciales de Google

#### 2a. Crear Google Cloud Project
1. Ve a [console.cloud.google.com](https://console.cloud.google.com)
2. Crea un nuevo proyecto
3. Habilita las siguientes APIs:
   - **Google Ads API**
   - **Google Analytics Data API**
   - **Google Analytics Admin API**

#### 2b. Crear credenciales OAuth 2.0
1. En "APIs & Services" → "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
2. Tipo: **Desktop Application**
3. Descarga el JSON y guárdalo como `~/.adloop/credentials.json`

#### 2c. Obtener Developer Token de Google Ads
1. Ve a [ads.google.com](https://ads.google.com) → tu cuenta → "Tools & Settings" → "API Center"
2. Copia tu Developer Token

### 3. Crear el archivo de configuración

```bash
mkdir -p ~/.adloop
```

Crea `~/.adloop/config.yaml`:

```yaml
google:
  project_id: "tu-gcp-project-id"
  credentials_path: "~/.adloop/credentials.json"
  token_path: "~/.adloop/token.json"

ga4:
  property_id: "123456789"  # Tu GA4 Property ID

ads:
  developer_token: "tu-developer-token"
  customer_id: "1234567890"      # Sin guiones
  login_customer_id: "1234567890"  # MCC account si aplica

safety:
  max_daily_budget: 100.0       # Límite máximo en USD
  max_bid_increase_pct: 50      # Máximo % de aumento de bid
  require_dry_run: true         # Siempre hacer dry-run primero
  log_file: "~/.adloop/audit.log"
```

### 4. Primera autenticación

```bash
cd ~/adloop
python -m adloop
```

Se abrirá el navegador para autenticar con Google. Acepta los permisos y el token se guardará en `~/.adloop/token.json`.

---

## Configuración en Claude Desktop

Edita `%APPDATA%\Claude\claude_desktop_config.json` (Windows) o `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac):

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python",
      "args": ["-m", "adloop"],
      "cwd": "C:/Users/TU_USUARIO/adloop",
      "env": {
        "ADLOOP_CONFIG": "C:/Users/TU_USUARIO/.adloop/config.yaml"
      }
    }
  }
}
```

> **Windows con uv:** usa la ruta completa al Python del virtualenv:
> `"command": "C:/Users/TU_USUARIO/adloop/.venv/Scripts/python.exe"`

Reinicia Claude Desktop.

---

## Configuración en Claude Code

Ejecuta en tu proyecto o globalmente:

```bash
claude mcp add google-ads python -- -m adloop
```

O agrega manualmente a `.mcp.json` en la raíz de tu proyecto:

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

---

## Instalar las Skills en Claude Code

Las Skills proporcionan comandos `/` para flujos de trabajo predefinidos:

```bash
# Copiar las skills al directorio de Claude
cp -r skills/google-ads-analyze ~/.claude/skills/
cp -r skills/google-ads-manage ~/.claude/skills/
cp -r skills/google-ads-ga4 ~/.claude/skills/
cp -r skills/google-ads-setup ~/.claude/skills/
```

Luego en Claude Code puedes usar:
- `/google-ads-analyze` — Analizar rendimiento
- `/google-ads-manage` — Gestionar campañas (con safety checks)
- `/google-ads-ga4` — Consultar GA4
- `/google-ads-setup` — Verificar configuración

---

## Herramientas MCP disponibles

### Lectura (Google Ads)
| Herramienta | Descripción |
|-------------|-------------|
| `list_accounts` | Lista todas las cuentas accesibles |
| `get_campaign_performance` | Métricas de campañas (impresiones, clics, costo, conversiones) |
| `get_ad_performance` | Rendimiento a nivel de anuncio |
| `get_keyword_performance` | Keywords con Quality Score y bid info |
| `get_search_terms` | Términos de búsqueda reales (últimos 30 días) |
| `run_gaql` | Query GAQL personalizada |

### Lectura (GA4)
| Herramienta | Descripción |
|-------------|-------------|
| `get_account_summaries` | Descubrir cuentas y propiedades GA4 |
| `run_ga4_report` | Reporte personalizado con dimensiones y métricas |
| `run_realtime_report` | Usuarios activos en tiempo real |
| `get_tracking_events` | Eventos de tracking configurados |

### Escritura (3 pasos: draft → preview → confirm)
| Herramienta | Descripción |
|-------------|-------------|
| `draft_responsive_search_ad` | Crear borrador de anuncio RSA |
| `draft_keywords` | Agregar keywords (borrador) |
| `add_negative_keywords` | Agregar negative keywords |
| `pause_entity` | Pausar campaña/ad group/anuncio |
| `enable_entity` | Activar campaña/ad group/anuncio |
| `remove_entity` | Eliminar entidad |
| `confirm_and_apply` | Ejecutar cambios (dry_run=true por defecto) |

---

## Sistema de seguridad

Todas las operaciones de escritura siguen este flujo:

```
Usuario pide cambio
    ↓
draft_*() → Genera plan con UUID, valida límites
    ↓
Vista previa → Claude muestra qué cambiará
    ↓
confirm_and_apply(plan_id, dry_run=True)  ← Simulación primero
    ↓
confirm_and_apply(plan_id, dry_run=False) ← Solo con confirmación explícita
```

**Protecciones activas:**
- Cap de presupuesto diario máximo
- Límite de aumento de bids
- Operaciones bloqueadas configurables
- Log de auditoría de todas las acciones
- Nuevos anuncios se crean en estado **pausado** por defecto

---

## Ejemplos de uso

### En Claude Code o Claude Desktop:

```
Muéstrame el rendimiento de mis campañas del último mes para la cuenta 1234567890

¿Cuáles son los términos de búsqueda con mayor costo y sin conversiones?

Pausa la campaña "Brand - Exact" (ID: 987654321) de la cuenta 1234567890

Crea un anuncio RSA para el grupo de anuncios 555444333 con estas headlines: [...]

¿Cuántos usuarios activos hay en GA4 ahora mismo?
```

---

## Estructura del proyecto

```
google-ads-mcp/
├── README.md
├── .gitignore
├── install.sh              # Script de instalación automática
├── skills/
│   ├── google-ads-analyze/ # Skill de análisis (/google-ads-analyze)
│   ├── google-ads-manage/  # Skill de gestión (/google-ads-manage)
│   ├── google-ads-ga4/     # Skill de GA4 (/google-ads-ga4)
│   └── google-ads-setup/   # Skill de setup (/google-ads-setup)
├── config/
│   ├── adloop-config.yaml.example
│   ├── claude-desktop-config.json.example
│   └── mcp.json.example
└── docs/
    └── troubleshooting.md
```

---

## Créditos

- **AdLoop** por [kLOsk](https://github.com/kLOsk/adloop) — MIT License
- Integración y Skills por Gabriel Urrutia
