# Google Ads Manager

Gestiona campañas de Google Ads de forma segura: crea anuncios, agrega keywords, pausa/activa entidades y aplica negative keywords. Usa un flujo de 3 pasos con confirmación explícita antes de cualquier cambio real.

## Cuándo usar esta skill

Úsala cuando el usuario pida:
- Pausar o activar campañas, grupos de anuncios o anuncios
- Crear nuevos anuncios de búsqueda responsivos (RSA)
- Agregar keywords a un grupo de anuncios
- Agregar negative keywords
- Eliminar entidades (con doble confirmación)

## IMPORTANTE: Flujo de seguridad obligatorio

**NUNCA ejecutes cambios directamente.** Siempre sigue este flujo:

```
1. draft_*()          → genera plan con UUID (no toca Google Ads)
2. Muestra preview    → describe exactamente qué cambiará
3. Pide confirmación  → espera "sí, confirma" del usuario
4. confirm_and_apply(plan_id, dry_run=True)   → simulación primero
5. Confirma el dry-run con el usuario
6. confirm_and_apply(plan_id, dry_run=False)  → solo con OK explícito
```

Si el usuario dice "hazlo directamente" o "sin confirmación", responde:
> "Por seguridad, el sistema siempre hace un dry-run antes de aplicar cambios reales. Es solo un paso extra que protege tu cuenta."

---

## Operaciones disponibles

### Pausar una entidad

**Cuándo:** el usuario quiere desactivar temporalmente una campaña, grupo o anuncio.

```python
# Paso 1: Draft
pause_entity(
  entity_type="campaign",  # "campaign" | "ad_group" | "ad"
  entity_id="123456789",
  customer_id="1234567890"
)
# Retorna: plan_id, preview del cambio

# Paso 2: Muestra preview al usuario
# Paso 3: Pide confirmación
# Paso 4: Dry run
confirm_and_apply(plan_id="uuid-aqui", dry_run=True)
# Paso 5: Confirma con usuario que el dry-run fue exitoso
# Paso 6: Aplicar real
confirm_and_apply(plan_id="uuid-aqui", dry_run=False)
```

### Activar una entidad

```python
enable_entity(
  entity_type="campaign",  # "campaign" | "ad_group" | "ad"
  entity_id="123456789",
  customer_id="1234567890"
)
```
Luego sigue el mismo flujo de confirmación.

### Eliminar una entidad

**REQUIERE DOBLE CONFIRMACIÓN.** Es una operación irreversible.

```python
remove_entity(
  entity_type="ad",  # "campaign" | "ad_group" | "ad" | "keyword"
  entity_id="123456789",
  customer_id="1234567890"
)
```

Antes de iniciar, di: "Eliminar [entidad] es irreversible. ¿Estás seguro? Escribe 'confirmo eliminación' para continuar."

### Crear anuncio RSA (Responsive Search Ad)

**Reglas de validación:**
- Mínimo 3 headlines, máximo 15
- Mínimo 2 descriptions, máximo 4
- Headlines: máximo 30 caracteres cada uno
- Descriptions: máximo 90 caracteres cada uno
- Final URL: debe incluir el protocolo (https://)

```python
draft_responsive_search_ad(
  customer_id="1234567890",
  ad_group_id="987654321",
  headlines=[
    "Headline 1",
    "Headline 2",
    "Headline 3"
  ],
  descriptions=[
    "Description 1 hasta 90 caracteres",
    "Description 2 hasta 90 caracteres"
  ],
  final_url="https://ejemplo.com/landing-page",
  path1="categoria",    # opcional, hasta 15 chars
  path2="subcategoria"  # opcional, hasta 15 chars
)
```

**Nota:** los anuncios nuevos se crean en estado **PAUSED** por defecto. Usa `enable_entity` después si el usuario quiere activarlos.

### Agregar keywords

```python
draft_keywords(
  customer_id="1234567890",
  ad_group_id="987654321",
  keywords=[
    {"text": "mi keyword", "match_type": "EXACT"},
    {"text": "otra keyword", "match_type": "PHRASE"},
    {"text": "broad keyword", "match_type": "BROAD"}
  ],
  bids={
    "mi keyword": 1.50  # CPC máximo en USD, opcional
  }
)
```

Match types válidos: `EXACT`, `PHRASE`, `BROAD`

### Agregar negative keywords

```python
add_negative_keywords(
  customer_id="1234567890",
  negative_keywords=[
    {"text": "gratis", "match_type": "BROAD", "level": "campaign", "id": "campaña_id"},
    {"text": "tutorial", "match_type": "EXACT", "level": "ad_group", "id": "grupo_id"}
  ]
)
```

**Flujo recomendado para negativos:**
1. Usa `/google-ads-analyze` primero para obtener términos de búsqueda
2. Identifica los irrelevantes o de bajo rendimiento
3. Agrupa por tema para proponer negativos
4. Aplica con esta operación

---

## Cómo identificar IDs de entidades

Si el usuario no sabe el ID de una campaña/grupo/anuncio, usa GAQL:

**Buscar campaña por nombre:**
```sql
SELECT campaign.id, campaign.name, campaign.status
FROM campaign
WHERE campaign.name LIKE '%nombre%'
```

**Buscar grupos de anuncios:**
```sql
SELECT ad_group.id, ad_group.name, campaign.name
FROM ad_group
WHERE campaign.id = 123456789
```

**Buscar anuncios activos:**
```sql
SELECT ad_group_ad.ad.id, ad_group_ad.ad.final_urls,
       ad_group.name, campaign.name,
       ad_group_ad.status
FROM ad_group_ad
WHERE ad_group_ad.status = 'ENABLED'
  AND campaign.id = 123456789
```

---

## Presentación de cambios al usuario

Antes de confirmar, siempre muestra un resumen claro:

```
📋 Resumen del cambio propuesto:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Operación: PAUSAR campaña
Entidad: "Brand - Exact Match" (ID: 987654321)
Cuenta: 1234567890
Estado actual: ENABLED → PAUSED

Plan ID: abc-123-def (válido por 10 minutos)

¿Confirmas este cambio? Responde "sí, aplica" para continuar.
```

---

## Errores frecuentes y cómo manejarlos

| Error | Causa probable | Solución |
|-------|---------------|----------|
| `Budget cap exceeded` | El cambio supera `max_daily_budget` | Informar al usuario, pedir ajustar config |
| `Bid increase too large` | Supera `max_bid_increase_pct` | Proponer un aumento menor en pasos |
| `Plan not found` | El plan_id expiró | Volver a hacer el draft |
| `Entity not found` | ID incorrecto | Usar GAQL para buscar el ID correcto |
| `Insufficient permissions` | Sin acceso a esa cuenta | Verificar con `list_accounts` |

---

## Buenas prácticas

1. **Siempre analiza antes de cambiar**: sugiere revisar rendimiento antes de pausar/eliminar
2. **Agrupa negativos por tema**: más fácil de auditar después
3. **RSAs en PAUSED**: crea y revisa antes de activar
4. **Un cambio a la vez**: no apliques múltiples cambios críticos en una sola sesión sin revisar resultados
5. **Log de auditoría**: todos los cambios quedan en `~/.adloop/audit.log`
