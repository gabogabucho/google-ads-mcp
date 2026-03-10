#!/usr/bin/env bash
# install.sh — Instalador de google-ads-mcp para macOS y Linux
# Uso: bash install.sh
#
# Requiere: Python 3.11+, Git
# Para Windows usa install.ps1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/google-ads-mcp"
CONFIG_DIR="$HOME/.google-ads-mcp"
SKILLS_DIR="$HOME/.claude/skills"

echo ""
echo "=== google-ads-mcp — Instalador para macOS/Linux ==="
echo ""

# ── 1. Verificar Python ───────────────────────────────────────────────────────
echo "→ Verificando Python 3.11+..."
if ! command -v python3 &>/dev/null; then
    echo "  ERROR: Python 3 no encontrado."
    echo "  macOS:  brew install python@3.12"
    echo "  Ubuntu: sudo apt install python3.12"
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 11 ) ]]; then
    echo "  ERROR: Se requiere Python 3.11+. Versión actual: $PY_VER"
    exit 1
fi
echo "  Python $PY_VER encontrado."

# ── 2. Verificar / instalar uv ────────────────────────────────────────────────
echo "→ Verificando uv..."
if ! command -v uv &>/dev/null; then
    echo "  uv no encontrado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv &>/dev/null; then
    echo "  AVISO: uv instalado pero no en PATH. Reinicia la terminal y vuelve a ejecutar."
    exit 1
fi
echo "  uv $(uv --version) encontrado."

# ── 3. Verificar Git ──────────────────────────────────────────────────────────
echo "→ Verificando git..."
if ! command -v git &>/dev/null; then
    echo "  ERROR: git no encontrado."
    echo "  macOS:  xcode-select --install"
    echo "  Ubuntu: sudo apt install git"
    exit 1
fi
echo "  git encontrado."

# ── 4. Instalar el paquete ────────────────────────────────────────────────────
echo "→ Instalando google-ads-mcp en $INSTALL_DIR..."
if [[ "$SCRIPT_DIR" != "$INSTALL_DIR" ]]; then
    mkdir -p "$INSTALL_DIR"
    rsync -a --exclude='.git' --exclude='.venv' "$SCRIPT_DIR/" "$INSTALL_DIR/"
fi

cd "$INSTALL_DIR"
uv sync
echo "  Instalación completada."

# ── 5. Crear directorio de configuración ──────────────────────────────────────
echo "→ Creando directorio de configuración $CONFIG_DIR..."
mkdir -p "$CONFIG_DIR"

CONFIG_FILE="$CONFIG_DIR/config.yaml"
if [[ ! -f "$CONFIG_FILE" ]]; then
    cp "$SCRIPT_DIR/config/config.yaml.example" "$CONFIG_FILE"
    echo "  Archivo de config creado: $CONFIG_FILE"
    echo "  IMPORTANTE: Edita ese archivo con tus credenciales antes de continuar."
else
    echo "  Config ya existe: $CONFIG_FILE"
fi

# ── 6. Instalar Skills en Claude Code ─────────────────────────────────────────
echo "→ Instalando Skills en $SKILLS_DIR..."
mkdir -p "$SKILLS_DIR"

for skill in google-ads-analyze google-ads-manage google-ads-ga4 google-ads-setup; do
    if [[ -d "$SCRIPT_DIR/skills/$skill" ]]; then
        cp -r "$SCRIPT_DIR/skills/$skill" "$SKILLS_DIR/"
        echo "  Skill instalada: /$skill"
    fi
done

# ── 7. Detectar ruta del Python del venv ──────────────────────────────────────
PYTHON_PATH="$INSTALL_DIR/.venv/bin/python"

# ── 8. Determinar config de Claude Desktop ────────────────────────────────────
if [[ "$(uname)" == "Darwin" ]]; then
    CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
else
    CLAUDE_DESKTOP_CONFIG="$HOME/.config/Claude/claude_desktop_config.json"
fi

# ── 9. Mostrar instrucciones finales ──────────────────────────────────────────
echo ""
echo "=== Instalación completada ==="
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Edita la configuración:"
echo "   \$EDITOR $CONFIG_FILE"
echo ""
echo "2. Agrega esto a Claude Desktop ($CLAUDE_DESKTOP_CONFIG):"
echo '   "mcpServers": {'
echo '     "google-ads": {'
echo "       \"command\": \"$PYTHON_PATH\","
echo '       "args": ["-m", "google_ads_mcp"],'
echo '       "env": {'
echo "         \"GOOGLE_ADS_MCP_CONFIG\": \"$CONFIG_FILE\""
echo '       }'
echo '     }'
echo '   }'
echo ""
echo "3. Primera autenticación con Google:"
echo "   $PYTHON_PATH -m google_ads_mcp"
echo ""
echo "4. Reinicia Claude Desktop."
echo ""
echo "5. Skills disponibles en Claude Code:"
echo "   /google-ads-setup    — verificar instalación"
echo "   /google-ads-analyze  — analizar campañas"
echo "   /google-ads-manage   — gestionar campañas"
echo "   /google-ads-ga4      — consultar GA4"
echo ""
