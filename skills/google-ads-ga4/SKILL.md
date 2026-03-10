# Google Analytics 4 Analyzer

Consulta datos de GA4 y cruza con Google Ads para análisis de rendimiento completo.

## Cuándo usar esta skill

- Ver tráfico, conversiones o eventos en GA4
- Comparar canales (paid, organic, direct)
- Ver usuarios activos en tiempo real
- Verificar eventos de tracking configurados
- Analizar el funnel desde click de ad hasta conversión

## Flujo de trabajo

### 1. Descubrir propiedades

Si el usuario no tiene `property_id`:
```
list_ga4_properties()
```

### 2. Verificar tracking
```
get_ga4_events(property_id="123456789")
```
Retorna todos los eventos con su volumen en los últimos 30 días.

### 3. Reporte personalizado
```
run_ga4_report(
  property_id="123456789",
  dimensions=["sessionDefaultChannelGroup", "deviceCategory"],
  metrics=["sessions", "conversions", "totalRevenue", "bounceRate"],
  start_date="30daysAgo",
  end_date="today",
  limit=50
)
```

#### Dimensiones frecuentes
- `sessionDefaultChannelGroup` — canal (Paid Search, Organic, Direct…)
- `deviceCategory` — desktop / mobile / tablet
- `sessionCampaignName` — campaña de Google Ads
- `sessionGoogleAdsKeyword` — keyword que generó la sesión
- `landingPage` — página de entrada
- `country`, `city`, `date`

#### Métricas frecuentes
- `sessions`, `totalUsers`, `newUsers`
- `bounceRate`, `averageSessionDuration`, `engagementRate`
- `conversions`, `totalRevenue`

#### Rangos de fecha
- `"30daysAgo"` / `"7daysAgo"` / `"today"` / `"yesterday"`
- O formato: `"2024-01-01"`

### 4. Tiempo real
```
get_realtime_users(
  property_id="123456789",
  dimensions=["country", "deviceCategory"]
)
```

## Análisis frecuentes

### Rendimiento de Google Ads en GA4
```
run_ga4_report(
  dimensions=["sessionCampaignName", "sessionGoogleAdsKeyword"],
  metrics=["sessions", "conversions", "totalRevenue", "bounceRate"],
  start_date="30daysAgo", end_date="today"
)
```
Combina con `get_campaign_performance` de Ads para ver el ciclo completo.

### Análisis por dispositivo
```
run_ga4_report(
  dimensions=["deviceCategory"],
  metrics=["sessions", "conversions", "bounceRate"],
  start_date="30daysAgo", end_date="today"
)
```
Útil para justificar ajustes de bid por dispositivo.

### Verificar conversiones
1. `get_ga4_events()` → buscar el evento de conversión (purchase, lead_submit…)
2. Comparar volumen con lo que reporta Google Ads
3. Si hay discrepancia, investigar con reporte por `eventName` + `date`
