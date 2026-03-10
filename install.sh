#!/usr/bin/env bash
# install.sh — Setup automático de Google Ads MCP para Claude
# Uso: bash install.sh

set -e

ADLOOP_DIR="$HOME/adloop"
ADLOOP_CONFIG_DIR="$HOME/.adloop"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"

echo ""
echo "=== Google Ads MCP para Claude ==="
echo ""

# ─── 1. Verificar dependencias ─────────────────────────────────────────────

echo "→ Verificando Python 3.11+..."
if ! command -v python3 &>/dev/null; then
  echo "ERROR: Python 3 no encontrado. Instala Python 3.11+ desde python.org"
  exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python $PYTHON_VERSION encontrado."

echo "→ Verificando uv..."
if ! command -v uv &>/dev/null; then
  echo "  uv no encontrado. Instalando..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "  uv encontrado: $(uv --version)"

echo "→ Verificando git..."
if ! command -v git &>/dev/null; then
  echo "ERROR: git no encontrado. Instala git desde git-scm.com"
  exit 1
fi

# ─── 2. Clonar AdLoop ──────────────────────────────────────────────────────

if [ -d "$ADLOOP_DIR" ]; then
  echo "→ AdLoop ya existe en $ADLOOP_DIR. Actualizando..."
  cd "$ADLOOP_DIR" && git pull
else
  echo "→ Clonando AdLoop en $ADLOOP_DIR..."
  git clone https://github.com/kLOsk/adloop.git "$ADLOOP_DIR"
fi

echo "→ Instalando dependencias de AdLoop..."
cd "$ADLOOP_DIR"
uv sync

# ─── 3. Crear directorio de configuración ──────────────────────────────────

echo "→ Creando directorio $ADLOOP_CONFIG_DIR..."
mkdir -p "$ADLOOP_CONFIG_DIR"

if [ ! -f "$ADLOOP_CONFIG_DIR/config.yaml" ]; then
  echo "→ Copiando config de ejemplo..."
  cp "$(dirname "$0")/config/adloop-config.yaml.example" "$ADLOOP_CONFIG_DIR/config.yaml"
  echo ""
  echo "  IMPORTANTE: Edita $ADLOOP_CONFIG_DIR/config.yaml con tus credenciales."
  echo "  Ver README.md para instrucciones detalladas."
  echo ""
else
  echo "  Config ya existe en $ADLOOP_CONFIG_DIR/config.yaml"
fi

# ─── 4. Instalar Skills en Claude Code ─────────────────────────────────────

echo "→ Instalando Skills en $CLAUDE_SKILLS_DIR..."
mkdir -p "$CLAUDE_SKILLS_DIR"

SKILLS_DIR="$(dirname "$0")/skills"
for skill in google-ads-analyze google-ads-manage google-ads-ga4 google-ads-setup; do
  if [ -d "$SKILLS_DIR/$skill" ]; then
    cp -r "$SKILLS_DIR/$skill" "$CLAUDE_SKILLS_DIR/"
    echo "  Instalada: /$skill"
  fi
done

# ─── 5. Detectar OS para instrucciones de config ───────────────────────────

PYTHON_PATH="$ADLOOP_DIR/.venv/bin/python"
CONFIG_PATH="$ADLOOP_CONFIG_DIR/config.yaml"

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
  CLAUDE_DESKTOP_CONFIG="$APPDATA/Claude/claude_desktop_config.json"
  PYTHON_PATH="$ADLOOP_DIR/.venv/Scripts/python.exe"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
else
  CLAUDE_DESKTOP_CONFIG="$HOME/.config/Claude/claude_desktop_config.json"
fi

# ─── 6. Mostrar instrucciones finales ──────────────────────────────────────

echo ""
echo "=== Instalación completada ==="
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Edita la configuración de AdLoop:"
echo "   $ADLOOP_CONFIG_DIR/config.yaml"
echo ""
echo "2. Configura Claude Desktop."
echo "   Agrega esto a: $CLAUDE_DESKTOP_CONFIG"
echo ""
echo '   "mcpServers": {'
echo '     "google-ads": {'
echo "       \"command\": \"$PYTHON_PATH\","
echo '       "args": ["-m", "adloop"],'
echo '       "env": {'
echo "         \"ADLOOP_CONFIG\": \"$CONFIG_PATH\""
echo '       }'
echo '     }'
echo '   }'
echo ""
echo "3. Primera autenticación con Google:"
echo "   $PYTHON_PATH -m adloop"
echo ""
echo "4. Reinicia Claude Desktop."
echo ""
echo "5. En Claude Code, usa:"
echo "   /google-ads-setup  — verificar instalación"
echo "   /google-ads-analyze — analizar campañas"
echo "   /google-ads-manage  — gestionar campañas"
echo "   /google-ads-ga4     — consultar GA4"
echo ""
