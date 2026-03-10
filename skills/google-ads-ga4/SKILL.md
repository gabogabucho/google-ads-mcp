# Google Analytics 4 (GA4) Analyzer

Consulta datos de Google Analytics 4 usando el servidor MCP adloop. Combina datos de GA4 con Google Ads para análisis de rendimiento end-to-end.

## Cuándo usar esta skill

Úsala cuando el usuario pida:
- Ver tráfico, conversiones o eventos en GA4
- Comparar rendimiento de canales (paid, organic, direct)
- Ver usuarios activos en tiempo real
- Verificar qué eventos de tracking están configurados
- Analizar el funnel desde click de ad hasta conversión

---

## Flujo de trabajo

### Paso 1: Descubrir cuentas y propiedades

Si el usuario no tiene configurado un `property_id`:

```python
get_account_summaries()
```

Muestra la lista de propiedades GA4 accesibles y pide al usuario que elija.

### Paso 2: Verificar eventos de tracking

```python
get_tracking_events()
```

Retorna: nombres de eventos configurados y volumen en los últimos 30 días. Útil para verificar que el tracking de conversiones funciona correctamente.

### Paso 3: Reportes personalizados

```python
run_ga4_report(
  dimensions=["sessionDefaultChannelGroup", "deviceCategory"],
  metrics=["sessions", "conversions", "totalRevenue"],
  date_range={"start_date": "30daysAgo", "end_date": "today"},
  limit=50
)
```

#### Dimensiones comunes
| Dimensión | Descripción |
|-----------|-------------|
| `sessionDefaultChannelGroup` | Canal (Paid Search, Organic, Direct, etc.) |
| `deviceCategory` | desktop / mobile / tablet |
| `country` | País |
| `city` | Ciudad |
| `landingPage` | Página de entrada |
| `sessionCampaignName` | Nombre de campaña |
| `sessionGoogleAdsAdGroupName` | Grupo de anuncios |
| `sessionGoogleAdsKeyword` | Keyword que generó la sesión |
| `pagePath` | Ruta de la página |
| `date` | Fecha |
| `week` | Semana |
| `month` | Mes |

#### Métricas comunes
| Métrica | Descripción |
|---------|-------------|
| `sessions` | Sesiones |
| `totalUsers` | Usuarios únicos |
| `newUsers` | Nuevos usuarios |
| `bounceRate` | Tasa de rebote |
| `averageSessionDuration` | Duración promedio de sesión |
| `conversions` | Total de conversiones |
| `totalRevenue` | Revenue total |
| `engagementRate` | Tasa de engagement |
| `screenPageViews` | Páginas vistas |
| `eventCount` | Total de eventos |

#### Rangos de fecha comunes
- `"7daysAgo"` a `"today"` → última semana
- `"30daysAgo"` a `"today"` → último mes
- `"2024-01-01"` a `"2024-01-31"` → rango específico
- `"yesterday"` a `"yesterday"` → ayer exacto

### Paso 4: Tiempo real

```python
run_realtime_report(
  dimensions=["country", "deviceCategory"],
  metrics=["activeUsers"]
)
```

Útil para verificar: ¿está llegando tráfico de una campaña recién activada?

---

## Análisis frecuentes

### Rendimiento de Google Ads en GA4

```python
run_ga4_report(
  dimensions=["sessionCampaignName", "sessionGoogleAdsAdGroupName"],
  metrics=["sessions", "conversions", "totalRevenue", "bounceRate"],
  date_range={"start_date": "30daysAgo", "end_date": "today"},
  limit=100
)
```

Combina con `get_campaign_performance` de Google Ads para ver el ciclo completo: impresión → clic → sesión → conversión.

### Análisis por dispositivo

```python
run_ga4_report(
  dimensions=["deviceCategory", "sessionDefaultChannelGroup"],
  metrics=["sessions", "conversions", "totalRevenue"],
  date_range={"start_date": "30daysAgo", "end_date": "today"}
)
```

Útil para justificar ajustes de bid por dispositivo en Google Ads.

### Análisis de landing pages

```python
run_ga4_report(
  dimensions=["landingPage"],
  metrics=["sessions", "bounceRate", "conversions", "averageSessionDuration"],
  date_range={"start_date": "30daysAgo", "end_date": "today"},
  limit=20
)
```

Identifica páginas con alto bounce rate para recomendar mejoras o cambiar la URL de destino en los anuncios.

### Verificar tracking de conversiones

1. `get_tracking_events()` → ver eventos disponibles
2. Buscar el evento de conversión (e.g., `purchase`, `lead_form_submit`, `sign_up`)
3. Verificar volumen vs lo que reporta Google Ads
4. Si hay discrepancia, investigar con:

```python
run_ga4_report(
  dimensions=["eventName", "date"],
  metrics=["eventCount", "conversions"],
  date_range={"start_date": "30daysAgo", "end_date": "today"}
)
```

---

## Integración Google Ads + GA4

Para un análisis completo, combina ambas fuentes:

1. **Google Ads** → costo, clics, impresiones, CTR, CPC
2. **GA4** → sesiones, bounce rate, conversiones, revenue, duración

Ejemplo de flujo completo:
```
1. get_campaign_performance(customer_id, last_30_days)
   → Identifica campañas con alto gasto

2. run_ga4_report(dimensions=["sessionCampaignName"], metrics=["sessions", "bounceRate", "conversions"])
   → Verifica calidad del tráfico que llega

3. Cruza datos: costo alto + bounce rate alto = problema de relevancia
4. Recomienda: mejorar landing page o revisar targeting
```

---

## Presentación de resultados

Siempre presenta:
1. **Tabla de datos** con las métricas solicitadas
2. **Insights clave**: qué canales/campañas/dispositivos tienen mejor rendimiento
3. **Alertas**: bounce rate > 80%, sesiones sin conversiones con alto volumen
4. **Siguiente paso**: ¿conectar con datos de Google Ads? ¿ajustar bids por dispositivo?
