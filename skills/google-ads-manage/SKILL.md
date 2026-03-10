# Google Ads Manager

Gestiona campañas de forma segura: pausa/activa entidades, crea RSAs, agrega negative keywords.
Usa siempre el flujo **preview → confirm** antes de aplicar cualquier cambio real.

## Cuándo usar esta skill

- Pausar o activar campañas, grupos de anuncios o anuncios
- Crear nuevos anuncios RSA
- Agregar negative keywords

## Flujo de seguridad OBLIGATORIO

```
1. preview_*()              → genera plan con ID, no toca Google Ads
2. Muestra preview al usuario → describe exactamente qué cambiará
3. Pide confirmación explícita
4. apply_change(plan_id, dry_run=True)   → simulación primero
5. Confirma resultado del dry-run
6. apply_change(plan_id, dry_run=False)  → solo con OK del usuario
```

**NUNCA llames `apply_change(dry_run=False)` sin confirmación previa del usuario.**

---

## Pausar / activar / eliminar campaña

```python
# Paso 1: preview
preview_campaign_status_change(
  customer_id="1234567890",
  campaign_id="987654321",
  action="pause"   # "pause" | "enable" | "remove"
)
# Retorna: descripción del cambio y plan_id

# Paso 2-5: mostrar, confirmar, dry-run
apply_change(plan_id="abc123", dry_run=True)

# Paso 6: aplicar real
apply_change(plan_id="abc123", dry_run=False)
```

**Nota:** `remove` es irreversible. Pide confirmación doble: "¿Estás seguro? Escribe 'confirmo eliminación' para continuar."

## Agregar negative keywords

```python
preview_add_negative_keywords(
  customer_id="1234567890",
  keywords=["gratis", "tutorial", "cómo hacer"],
  match_type="BROAD",         # "BROAD" | "PHRASE" | "EXACT"
  campaign_id="987654321",    # nivel campaña, O...
  # ad_group_id="555444333",  # nivel grupo de anuncios
)
```

Flujo recomendado:
1. Usa `/google-ads-analyze` → `get_search_terms` para identificar los términos
2. Agrupa los irrelevantes por tema
3. Aplica como negativas con esta operación

## Crear anuncio RSA

**Validaciones:**
- Headlines: mínimo 3, máximo 15, cada uno ≤ 30 caracteres
- Descriptions: mínimo 2, máximo 4, cada una ≤ 90 caracteres
- URL: debe empezar con `https://`

```python
preview_responsive_search_ad(
  customer_id="1234567890",
  ad_group_id="555444333",
  final_url="https://ejemplo.com/landing",
  headlines=["Headline 1", "Headline 2", "Headline 3"],
  descriptions=["Description 1 hasta 90 chars", "Description 2"],
  path1="categoria",    # opcional, ≤ 15 chars
  path2="producto",     # opcional, ≤ 15 chars
)
```

Los RSAs siempre se crean en estado **PAUSED**. Para activar, usa `preview_campaign_status_change` a nivel del anuncio después de revisar.

## Encontrar IDs de entidades

Si el usuario no sabe el ID:
```
run_gaql_query(
  customer_id="1234567890",
  query="SELECT campaign.id, campaign.name, campaign.status FROM campaign WHERE campaign.name LIKE '%marca%'"
)
```

## Presentación del preview al usuario

Siempre muestra el contenido del plan antes de pedir confirmación:

```
📋 Cambio propuesto:
━━━━━━━━━━━━━━━━━━
Operación: PAUSAR campaña
Entidad: "Brand - Exact" (ID: 987654321)
Cuenta: 1234567890
Plan ID: abc123

¿Confirmas? Responde "sí, aplica" para continuar.
```
