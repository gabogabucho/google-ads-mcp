# Troubleshooting

## El MCP no aparece en Claude

**Síntoma:** Las herramientas `list_accounts`, `get_campaign_performance`, etc. no están disponibles.

**Soluciones:**
1. Verificar que la ruta de Python en la config apunta al virtualenv de adloop
2. Reiniciar Claude Desktop completamente (no solo cerrar ventana)
3. En Claude Code: ejecutar `claude mcp list` para ver si aparece "google-ads"
4. Revisar logs: en Claude Desktop, menú Developer → Show Logs

---

## Error: `ModuleNotFoundError: No module named 'adloop'`

El servidor MCP no encuentra el paquete. Causa: la ruta de Python en la configuración apunta al Python del sistema, no al virtualenv.

**Fix:** Usa la ruta absoluta al Python del virtualenv:
- Mac/Linux: `/Users/usuario/adloop/.venv/bin/python`
- Windows: `C:\Users\usuario\adloop\.venv\Scripts\python.exe`

Verifica con:
```bash
~/adloop/.venv/bin/python -c "import adloop; print('OK')"
```

---

## Error: `FileNotFoundError: ~/.adloop/credentials.json`

El archivo de credenciales OAuth no existe en la ruta configurada.

**Fix:**
1. Descarga el JSON desde Google Cloud Console (APIs & Services → Credentials)
2. Guárdalo exactamente en la ruta especificada en `config.yaml` bajo `google.credentials_path`
3. Verifica que la ruta tenga tilde expandida: `~/.adloop/` = `/Users/usuario/.adloop/`

---

## Error: `Token has been expired or revoked`

El token de OAuth ha expirado o fue revocado.

**Fix:**
```bash
rm ~/.adloop/token.json
~/adloop/.venv/bin/python -m adloop
# Se abrirá el navegador para re-autenticar
```

---

## Error: `Access denied: Developer token has not been approved`

El Developer Token de Google Ads está en nivel TEST y no puede acceder a cuentas de producción.

**Opciones:**
1. **Para pruebas:** usa una cuenta de prueba de Google Ads (test account) con el token TEST
2. **Para producción:** solicitar aprobación del token en Google Ads → Tools → API Center

El proceso de aprobación puede tomar varios días.

---

## Error: `Customer ID not found` o `Invalid customer ID`

**Causas posibles:**
1. El ID tiene guiones (123-456-7890) cuando debería ser solo números (1234567890)
2. La cuenta no es accesible con las credenciales actuales
3. El `login_customer_id` (MCC) no tiene acceso a ese `customer_id`

**Fix:**
```python
# Usa list_accounts() para ver las cuentas accesibles
list_accounts()
```

---

## Error de límites de seguridad (`Budget cap exceeded`)

El cambio propuesto supera el `max_daily_budget` configurado en `config.yaml`.

**Fix:** Edita `~/.adloop/config.yaml` y aumenta `safety.max_daily_budget`. Luego reinicia el servidor MCP.

---

## El servidor MCP se desconecta frecuentemente

**Causas posibles:**
1. El proceso Python se cae por un error interno
2. El token de Google expiró y el servidor no lo maneja

**Solución temporal:** Reiniciar Claude Desktop regenera la conexión MCP.

**Solución permanente:** Revisar logs del servidor. En Claude Desktop: Developer → MCP Logs.

---

## Las skills `/google-ads-*` no aparecen en Claude Code

Las skills deben estar en `~/.claude/skills/`:

```bash
ls ~/.claude/skills/
# Debe mostrar: google-ads-analyze  google-ads-manage  google-ads-ga4  google-ads-setup
```

Si no están:
```bash
cp -r /ruta/a/google-ads-mcp/skills/google-ads-* ~/.claude/skills/
```

---

## Datos de GA4 no coinciden con Google Ads

Es normal una discrepancia del 5-15% entre los datos de GA4 y Google Ads por:
- Diferencia de atribución (last-click vs data-driven)
- Filtros de bots y spam en GA4
- Usuarios con cookies bloqueadas

Para análisis precisos, define un modelo de atribución común y compara tendencias, no números absolutos.
