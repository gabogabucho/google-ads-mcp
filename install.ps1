# install.ps1 — Instalador de google-ads-mcp para Windows
# Uso: powershell -ExecutionPolicy Bypass -File install.ps1
#
# Requiere: Python 3.11+, Git

$ErrorActionPreference = "Stop"

$InstallDir  = "$env:USERPROFILE\google-ads-mcp"
$ConfigDir   = "$env:USERPROFILE\.google-ads-mcp"
$SkillsDir   = "$env:USERPROFILE\.claude\skills"
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "=== google-ads-mcp — Instalador para Windows ===" -ForegroundColor Cyan
Write-Host ""

# ── 1. Verificar Python ───────────────────────────────────────────────────────
Write-Host "→ Verificando Python 3.11+..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    if ($pyVersion -notmatch "Python 3\.(1[1-9]|[2-9]\d)") {
        Write-Host "  ERROR: Se requiere Python 3.11+. Versión actual: $pyVersion" -ForegroundColor Red
        Write-Host "  Descarga desde: https://www.python.org/downloads/"
        exit 1
    }
    Write-Host "  $pyVersion encontrado." -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python no encontrado en PATH." -ForegroundColor Red
    Write-Host "  Descarga desde: https://www.python.org/downloads/"
    exit 1
}

# ── 2. Verificar / instalar uv ────────────────────────────────────────────────
Write-Host "→ Verificando uv..." -ForegroundColor Yellow
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "  uv no encontrado. Instalando..." -ForegroundColor Yellow
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    # Recargar PATH en la sesión actual
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + $env:PATH
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "  AVISO: uv instalado pero no en PATH. Reinicia PowerShell y vuelve a ejecutar." -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "  uv $(uv --version) encontrado." -ForegroundColor Green

# ── 3. Verificar Git ──────────────────────────────────────────────────────────
Write-Host "→ Verificando git..." -ForegroundColor Yellow
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: git no encontrado. Instala desde: https://git-scm.com/" -ForegroundColor Red
    exit 1
}
Write-Host "  git encontrado." -ForegroundColor Green

# ── 4. Instalar el paquete ────────────────────────────────────────────────────
Write-Host "→ Instalando google-ads-mcp en $InstallDir..." -ForegroundColor Yellow
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
    Copy-Item -Path "$ScriptDir\*" -Destination $InstallDir -Recurse -Force
}

Set-Location $InstallDir
uv sync
Write-Host "  Instalación completada." -ForegroundColor Green

# ── 5. Crear directorio de configuración ──────────────────────────────────────
Write-Host "→ Creando directorio de configuración $ConfigDir..." -ForegroundColor Yellow
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir | Out-Null
}

$ConfigFile = "$ConfigDir\config.yaml"
if (-not (Test-Path $ConfigFile)) {
    Copy-Item "$ScriptDir\config\config.yaml.example" $ConfigFile
    Write-Host "  Archivo de config creado: $ConfigFile" -ForegroundColor Green
    Write-Host "  IMPORTANTE: Edita ese archivo con tus credenciales antes de continuar." -ForegroundColor Yellow
} else {
    Write-Host "  Config ya existe: $ConfigFile" -ForegroundColor Green
}

# ── 6. Instalar Skills en Claude Code ─────────────────────────────────────────
Write-Host "→ Instalando Skills en $SkillsDir..." -ForegroundColor Yellow
if (-not (Test-Path $SkillsDir)) {
    New-Item -ItemType Directory -Path $SkillsDir | Out-Null
}

$skills = @("google-ads-analyze", "google-ads-manage", "google-ads-ga4", "google-ads-setup")
foreach ($skill in $skills) {
    $src = "$ScriptDir\skills\$skill"
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $SkillsDir -Recurse -Force
        Write-Host "  Skill instalada: /$skill" -ForegroundColor Green
    }
}

# ── 7. Detectar ruta del Python del venv ──────────────────────────────────────
$PythonPath = "$InstallDir\.venv\Scripts\python.exe"

# ── 8. Mostrar instrucciones finales ──────────────────────────────────────────
$ClaudeDesktopConfig = "$env:APPDATA\Claude\claude_desktop_config.json"

Write-Host ""
Write-Host "=== Instalación completada ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor White
Write-Host ""
Write-Host "1. Edita la configuración:" -ForegroundColor Yellow
Write-Host "   notepad $ConfigFile"
Write-Host ""
Write-Host "2. Agrega esto a Claude Desktop ($ClauseDesktopConfig):" -ForegroundColor Yellow
Write-Host '   "mcpServers": {'
Write-Host '     "google-ads": {'
Write-Host "       `"command`": `"$PythonPath`","
Write-Host '       "args": ["-m", "google_ads_mcp"],'
Write-Host '       "env": {'
Write-Host "         `"GOOGLE_ADS_MCP_CONFIG`": `"$ConfigFile`""
Write-Host '       }'
Write-Host '     }'
Write-Host '   }'
Write-Host ""
Write-Host "3. Primera autenticación con Google:" -ForegroundColor Yellow
Write-Host "   & `"$PythonPath`" -m google_ads_mcp"
Write-Host ""
Write-Host "4. Reinicia Claude Desktop." -ForegroundColor Yellow
Write-Host ""
Write-Host "5. Skills disponibles en Claude Code:" -ForegroundColor Yellow
Write-Host "   /google-ads-setup    — verificar instalación"
Write-Host "   /google-ads-analyze  — analizar campañas"
Write-Host "   /google-ads-manage   — gestionar campañas"
Write-Host "   /google-ads-ga4      — consultar GA4"
Write-Host ""
