# Google Ads Analyzer

Analiza el rendimiento de cuentas, campañas, anuncios y keywords usando las tools del MCP `google-ads`.

## Cuándo usar esta skill

- Ver rendimiento de campañas, anuncios o keywords
- Analizar términos de búsqueda y encontrar negative keywords
- Comparar métricas, identificar desperdicio de presupuesto
- Ejecutar queries GAQL personalizadas

## Flujo de trabajo

### Paso 1: Identificar la cuenta

Si el usuario no dio un `customer_id`:
```
list_google_ads_accounts()
```
Muestra la lista y pide que elija.

### Paso 2: Definir rango de fechas

Por defecto usa los últimos 30 días. Formato: `YYYY-MM-DD`.

### Paso 3: Obtener datos

**Campañas:**
```
get_campaign_performance(customer_id="1234567890", start_date="2024-01-01", end_date="2024-01-31")
```

**Anuncios:**
```
get_ad_performance(customer_id="1234567890", start_date="2024-01-01", end_date="2024-01-31")
```

**Keywords:**
```
get_keyword_performance(customer_id="1234567890", start_date="2024-01-01", end_date="2024-01-31")
```

**Términos de búsqueda:**
```
get_search_terms(customer_id="1234567890", start_date="2024-01-01", end_date="2024-01-31")
```

**Query GAQL personalizada:**
```
run_gaql_query(
  customer_id="1234567890",
  query="SELECT campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC LIMIT 10"
)
```

### Paso 4: Presentar resultados

1. **Resumen ejecutivo**: métricas clave y tendencias
2. **Top performers**: las mejores entidades por la métrica principal
3. **Alertas**: CTR bajo, QS < 5, alto costo sin conversiones
4. **Recomendaciones**: acciones priorizadas

## Análisis frecuentes

### Diagnóstico de cuenta
1. `get_campaign_performance` → estado general
2. `get_keyword_performance` → keywords con QS bajo
3. `get_search_terms` → términos irrelevantes

### Keywords candidatas a negativas
Buscar con GAQL keywords con conversiones = 0 y costo > $5:
```sql
SELECT ad_group_criterion.keyword.text, metrics.cost_micros, metrics.conversions
FROM keyword_view
WHERE metrics.conversions = 0 AND metrics.cost_micros > 5000000
  AND segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

Al terminar, ofrece: "¿Quieres que aplique algún cambio? Puedo usar `/google-ads-manage` de forma segura."
