# Google Ads Analyzer

Analiza el rendimiento de cuentas, campañas, anuncios y keywords en Google Ads usando el servidor MCP adloop.

## Cuándo usar esta skill

Úsala cuando el usuario pida:
- Ver rendimiento de campañas, anuncios o keywords
- Analizar términos de búsqueda
- Comparar métricas entre periodos
- Identificar campañas con bajo rendimiento o alto desperdicio
- Ejecutar queries GAQL personalizadas
- Auditar una cuenta de Google Ads

## Flujo de trabajo

### Paso 1: Identificar la cuenta

Si el usuario no proporcionó un `customer_id`, usa primero:
```
list_accounts()
```
Muestra la lista y pide al usuario que elija la cuenta a analizar.

### Paso 2: Definir el rango de fechas

Si no se especifica, usa los últimos 30 días:
- `date_range_start`: hace 30 días en formato `YYYY-MM-DD`
- `date_range_end`: hoy en formato `YYYY-MM-DD`

Periodos comunes:
- Última semana: últimos 7 días
- Último mes: últimos 30 días
- Este mes: desde el primer día del mes actual
- Trimestre: últimos 90 días

### Paso 3: Obtener los datos

Según lo que pida el usuario, llama a la herramienta correspondiente:

**Rendimiento de campañas:**
```
get_campaign_performance(
  customer_id="1234567890",
  date_range_start="2024-01-01",
  date_range_end="2024-01-31"
)
```
Métricas disponibles: impresiones, clics, costo, conversiones, CTR, CPC, CPA, ROAS.

**Rendimiento de anuncios:**
```
get_ad_performance(
  customer_id="1234567890",
  date_range_start="2024-01-01",
  date_range_end="2024-01-31"
)
```
Incluye headlines, descriptions, URLs y estado del anuncio.

**Rendimiento de keywords:**
```
get_keyword_performance(
  customer_id="1234567890",
  date_range_start="2024-01-01",
  date_range_end="2024-01-31"
)
```
Incluye Quality Score, match type, bid actual y competitivo.

**Términos de búsqueda:**
```
get_search_terms(
  customer_id="1234567890",
  date_range_start="2024-01-01",
  date_range_end="2024-01-31"
)
```
Retorna hasta 200 términos. Ideal para encontrar negativos potenciales.

**Query GAQL personalizada:**
```
run_gaql(
  query="SELECT campaign.name, metrics.clicks, metrics.cost_micros FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC LIMIT 10",
  customer_id="1234567890",
  output_format="table"
)
```

### Paso 4: Analizar y presentar resultados

Siempre presenta los resultados de forma estructurada:

1. **Resumen ejecutivo**: métricas clave y tendencias principales
2. **Top performers**: las 5 mejores entidades por la métrica principal
3. **Problemas detectados**: alto costo sin conversiones, bajo CTR, Quality Score bajo
4. **Recomendaciones**: acciones concretas y priorizadas

## Análisis frecuentes

### Diagnóstico de cuenta
Llama en este orden:
1. `get_campaign_performance` → ver estado general
2. `get_keyword_performance` → identificar keywords con QS bajo
3. `get_search_terms` → encontrar términos irrelevantes
4. Presenta: campanias activas, gasto total, CPA promedio, principales problemas

### Análisis de desperdicio
Busca con GAQL:
```sql
SELECT campaign.name, ad_group.name, keywords.keyword.text,
       metrics.clicks, metrics.cost_micros, metrics.conversions
FROM keyword_view
WHERE metrics.conversions = 0
  AND metrics.cost_micros > 5000000
  AND segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

### Análisis de términos de búsqueda
1. Ejecuta `get_search_terms`
2. Identifica términos con clics pero sin conversiones y alto costo
3. Identifica términos irrelevantes para el negocio
4. Sugiere agregarlos como negativos (ofrece usar `/google-ads-manage` para aplicarlos)

### Rendimiento por dispositivo
```sql
SELECT campaign.name, segments.device, metrics.clicks,
       metrics.cost_micros, metrics.conversions
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
```

## Formato de respuesta

Usa tablas markdown para datos tabulares. Resalta valores problemáticos:
- CPA > objetivo: marcar como alto
- CTR < 2% en Search: marcar como bajo
- QS < 5: marcar como crítico
- Campañas sin conversiones en 30 días: marcar para revisión

Al final siempre ofrece: "¿Quieres que aplique alguno de estos cambios? Puedo usar `/google-ads-manage` para hacerlo de forma segura."
