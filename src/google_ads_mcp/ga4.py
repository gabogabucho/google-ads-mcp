"""Google Analytics 4 API operations (read-only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunRealtimeReportRequest,
    RunReportRequest,
)

from .auth import get_credentials


# ── Client factories ──────────────────────────────────────────────────────────

def make_ga4_client(credentials_path: str, token_path: str) -> BetaAnalyticsDataClient:
    creds = get_credentials(credentials_path, token_path)
    return BetaAnalyticsDataClient(credentials=creds)


def make_ga4_admin_client(credentials_path: str, token_path: str) -> AnalyticsAdminServiceClient:
    creds = get_credentials(credentials_path, token_path)
    return AnalyticsAdminServiceClient(credentials=creds)


# ── Read operations ───────────────────────────────────────────────────────────

def list_properties(admin_client: AnalyticsAdminServiceClient) -> List[Dict[str, str]]:
    """List all accessible GA4 accounts and properties."""
    properties = []
    for summary in admin_client.list_account_summaries().account_summaries:
        for prop in summary.property_summaries:
            properties.append({
                "account_name": summary.display_name,
                "account_id": summary.account.split("/")[-1],
                "property_name": prop.display_name,
                "property_id": prop.property.split("/")[-1],
            })
    return properties


def run_report(
    client: BetaAnalyticsDataClient,
    property_id: str,
    dimensions: List[str],
    metrics: List[str],
    start_date: str,
    end_date: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Run a custom GA4 report."""
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        limit=limit,
    )
    response = client.run_report(request)
    dim_headers = [h.name for h in response.dimension_headers]
    met_headers = [h.name for h in response.metric_headers]

    rows = []
    for row in response.rows:
        entry: Dict[str, Any] = {}
        for i, val in enumerate(row.dimension_values):
            entry[dim_headers[i]] = val.value
        for i, val in enumerate(row.metric_values):
            entry[met_headers[i]] = _parse_metric(val.value)
        rows.append(entry)
    return rows


def run_realtime(
    client: BetaAnalyticsDataClient,
    property_id: str,
    dimensions: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Return real-time active users, optionally broken down by dimensions."""
    request = RunRealtimeReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name=d) for d in (dimensions or ["country"])],
        metrics=[Metric(name="activeUsers")],
        limit=20,
    )
    response = client.run_realtime_report(request)
    dim_headers = [h.name for h in response.dimension_headers]

    rows = []
    for row in response.rows:
        entry: Dict[str, Any] = {"activeUsers": row.metric_values[0].value}
        for i, val in enumerate(row.dimension_values):
            entry[dim_headers[i]] = val.value
        rows.append(entry)
    return rows


def get_events(
    client: BetaAnalyticsDataClient,
    property_id: str,
) -> List[Dict[str, Any]]:
    """List all event names and their 30-day count."""
    return run_report(
        client,
        property_id=property_id,
        dimensions=["eventName"],
        metrics=["eventCount"],
        start_date="30daysAgo",
        end_date="today",
        limit=200,
    )


# ── helpers ───────────────────────────────────────────────────────────────────

def _parse_metric(value: str) -> Any:
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value
