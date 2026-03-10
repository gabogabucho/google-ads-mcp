"""Main MCP server — all tool definitions.

Each tool has a rich docstring that Claude uses to understand when and how to
call it. Tools return formatted markdown strings ready to present to the user.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from fastmcp import FastMCP

from .config import Config
from .safety import (
    Plan,
    SafetyError,
    audit_log,
    check_budget,
    check_operation_allowed,
    consume_plan,
    create_plan,
    get_plan,
)

mcp = FastMCP(
    "google-ads-mcp",
    description=(
        "Manage Google Ads campaigns and query Google Analytics 4 data. "
        "Read operations are safe and instant. Write operations use a "
        "preview → confirm flow to prevent accidental changes."
    ),
)


# ── Config (loaded once at startup) ──────────────────────────────────────────

@lru_cache(maxsize=1)
def _cfg() -> Config:
    return Config.load(os.environ.get("GOOGLE_ADS_MCP_CONFIG"))


def _ads_client():
    cfg = _cfg()
    from .ads import make_ads_client
    return make_ads_client(cfg.ads, cfg.google.credentials_path, cfg.google.token_path)


def _ga4_client():
    cfg = _cfg()
    from .ga4 import make_ga4_client
    return make_ga4_client(cfg.google.credentials_path, cfg.google.token_path)


def _ga4_admin_client():
    cfg = _cfg()
    from .ga4 import make_ga4_admin_client
    return make_ga4_admin_client(cfg.google.credentials_path, cfg.google.token_path)


# ── Formatting helpers ────────────────────────────────────────────────────────

def _table(headers: List[str], rows: List[List[str]]) -> str:
    widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    header_row = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    data_rows = ["| " + " | ".join(str(r[i]).ljust(widths[i]) for i in range(len(headers))) + " |" for r in rows]
    return "\n".join([header_row, sep] + data_rows)


def _err(msg: str) -> str:
    return f"**Error:** {msg}"


# ── Google Ads — Read tools ───────────────────────────────────────────────────

@mcp.tool()
def list_google_ads_accounts() -> str:
    """List all Google Ads accounts accessible with the current credentials.

    Use this first when the user hasn't specified a customer_id, or to
    discover which accounts are available.
    """
    try:
        from .ads import list_accounts
        accounts = list_accounts(_ads_client())
        if not accounts:
            return "No accessible Google Ads accounts found for these credentials."
        rows = [[a["customer_id"]] for a in accounts]
        return f"**{len(accounts)} accessible account(s):**\n\n" + _table(["Customer ID"], rows)
    except Exception as exc:
        return _err(str(exc))


@mcp.tool()
def get_campaign_performance(
    customer_id: str,
    start_date: str,
    end_date: str,
) -> str:
    """Get performance metrics for all campaigns in a Google Ads account.

    Returns impressions, clicks, cost (USD), conversions, CTR, and average CPC.
    Results are sorted by spend (highest first), limited to 100 campaigns.

    Args:
        customer_id: Google Ads account ID (with or without dashes, e.g. "123-456-7890")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    try:
        from .ads import get_campaign_performance as _get
        data = _get(_ads_client(), customer_id, start_date, end_date)
        if not data:
            return f"No campaign data found for account {customer_id} in the selected date range."

        rows = [
            [
                str(r["campaign_id"]),
                r["campaign_name"][:35],
                r["status"],
                f"{r['impressions']:,}",
                f"{r['clicks']:,}",
                f"${r['cost_usd']:.2f}",
                f"{r['conversions']:.1f}",
                f"{r['ctr_pct']:.2f}%",
                f"${r['avg_cpc_usd']:.2f}",
            ]
            for r in data
        ]
        table = _table(
            ["ID", "Campaign", "Status", "Impr.", "Clicks", "Cost", "Conv.", "CTR", "Avg CPC"],
            rows,
        )
        total_cost = sum(r["cost_usd"] for r in data)
        total_conv = sum(r["conversions"] for r in data)
        return (
            f"**Campaign performance — {start_date} to {end_date} (account {customer_id})**\n\n"
            f"{table}\n\n"
            f"**Totals:** ${total_cost:.2f} spend · {total_conv:.0f} conversions"
        )
    except Exception as exc:
        return _err(str(exc))


@mcp.tool()
def get_keyword_performance(
    customer_id: str,
    start_date: str,
    end_date: str,
) -> str:
    """Get performance metrics for all keywords in a Google Ads account.

    Returns keyword text, match type, Quality Score, bid, clicks, cost, and conversions.
    Useful for identifying low-QS keywords, high-spend with no conversions, and
    keywords that are candidates for negative keyword lists.

    Args:
        customer_id: Google Ads account ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    try:
        from .ads import get_keyword_performance as _get
        data = _get(_ads_client(), customer_id, start_date, end_date)
        if not data:
            return f"No keyword data found for account {customer_id} in the selected date range."

        rows = [
            [
                r["keyword"],
                r["match_type"][:7],
                str(r["quality_score"] or "N/A"),
                r["status"],
                r["campaign"][:20],
                f"{r['clicks']:,}",
                f"${r['cost_usd']:.2f}",
                f"{r['conversions']:.1f}",
            ]
            for r in data
        ]
        table = _table(
            ["Keyword", "Match", "QS", "Status", "Campaign", "Clicks", "Cost", "Conv."],
            rows,
        )
        low_qs = [r for r in data if r["quality_score"] and r["quality_score"] < 5]
        note = f"\n\n⚠️ **{len(low_qs)} keyword(s) with Quality Score < 5**" if low_qs else ""
        return (
            f"**Keyword performance — {start_date} to {end_date} (account {customer_id})**\n\n"
            f"{table}{note}"
        )
    except Exception as exc:
        return _err(str(exc))


@mcp.tool()
def get_search_terms(
    customer_id: str,
    start_date: str,
    end_date: str,
    limit: int = 200,
) -> str:
    """Get actual search terms that triggered ads in a Google Ads account.

    Essential for finding negative keyword opportunities and understanding
    real user intent. Returns the top terms by spend.

    Args:
        customer_id: Google Ads account ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        limit: Maximum number of terms to return (default 200)
    """
    try:
        from .ads import get_search_terms as _get
        data = _get(_ads_client(), customer_id, start_date, end_date, limit)
        if not data:
            return f"No search term data found for account {customer_id}."

        rows = [
            [
                r["search_term"][:45],
                r["campaign"][:20],
                f"{r['clicks']:,}",
                f"${r['cost_usd']:.2f}",
                f"{r['conversions']:.1f}",
                r["status"],
            ]
            for r in data
        ]
        table = _table(["Search Term", "Campaign", "Clicks", "Cost", "Conv.", "Status"], rows)
        zero_conv = [r for r in data if r["conversions"] == 0 and r["cost_usd"] > 5]
        note = (
            f"\n\n💡 **{len(zero_conv)} term(s) with $5+ spend and 0 conversions** — "
            f"review for negative keywords."
        ) if zero_conv else ""
        return (
            f"**Search terms — {start_date} to {end_date} (account {customer_id})**\n\n"
            f"{table}{note}"
        )
    except Exception as exc:
        return _err(str(exc))


@mcp.tool()
def get_ad_performance(
    customer_id: str,
    start_date: str,
    end_date: str,
) -> str:
    """Get performance metrics at the individual ad level for a Google Ads account.

    Useful for identifying underperforming ads, comparing creative variations,
    and finding ads to pause or improve.

    Args:
        customer_id: Google Ads account ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    try:
        from .ads import get_ad_performance as _get
        data = _get(_ads_client(), customer_id, start_date, end_date)
        if not data:
            return f"No ad data found for account {customer_id}."

        rows = [
            [
                str(r["ad_id"]),
                r["ad_type"][:12],
                r["status"],
                r["campaign"][:20],
                r["ad_group"][:20],
                f"{r['clicks']:,}",
                f"${r['cost_usd']:.2f}",
                f"{r['conversions']:.1f}",
                f"{r['ctr_pct']:.2f}%",
            ]
            for r in data
        ]
        table = _table(
            ["Ad ID", "Type", "Status", "Campaign", "Ad Group", "Clicks", "Cost", "Conv.", "CTR"],
            rows,
        )
        return (
            f"**Ad performance — {start_date} to {end_date} (account {customer_id})**\n\n"
            f"{table}"
        )
    except Exception as exc:
        return _err(str(exc))


@mcp.tool()
def run_gaql_query(
    customer_id: str,
    query: str,
) -> str:
    """Execute a custom Google Ads Query Language (GAQL) query.

    Use this for advanced analysis not covered by the other tools.
    GAQL syntax: SELECT fields FROM resource WHERE conditions ORDER BY ... LIMIT n

    Common resources: campaign, ad_group, keyword_view, search_term_view,
    ad_group_ad, campaign_criterion, ad_group_criterion

    Args:
        customer_id: Google Ads account ID
        query: A valid GAQL query string
    """
    try:
        from .ads import run_gaql
        rows = run_gaql(_ads_client(), customer_id, query)
        if not rows:
            return "Query returned no results."
        if len(rows) == 1:
            return f"**1 result:**\n```json\n{rows[0]}\n```"
        headers = list(rows[0].keys())
        table_rows = [[str(r.get(h, "")) for h in headers] for r in rows[:50]]
        table = _table(headers, table_rows)
        suffix = f"\n\n_(showing first 50 of {len(rows)} results)_" if len(rows) > 50 else ""
        return f"**{len(rows)} result(s):**\n\n{table}{suffix}"
    except Exception as exc:
        return _err(str(exc))


# ── Google Analytics 4 — Read tools ──────────────────────────────────────────

@mcp.tool()
def list_ga4_properties() -> str:
    """List all Google Analytics 4 accounts and properties accessible with current credentials.

    Use this when the user hasn't provided a GA4 property_id, or to discover
    which properties are available.
    """
    try:
        from .ga4 import list_properties
        props = list_properties(_ga4_admin_client())
        if not props:
            return "No accessible GA4 properties found."
        rows = [
            [p["account_name"], p["account_id"], p["property_name"], p["property_id"]]
            for p in props
        ]
        return (
            f"**{len(props)} GA4 property(ies) found:**\n\n"
            + _table(["Account", "Acct ID", "Property", "Property ID"], rows)
        )
    except Exception as exc:
        return _err(str(exc))


@mcp.tool()
def run_ga4_report(
    property_id: str,
    dimensions: List[str],
    metrics: List[str],
    start_date: str,
    end_date: str,
    limit: int = 100,
) -> str:
    """Run a custom Google Analytics 4 report.

    Common dimensions: sessionDefaultChannelGroup, deviceCategory, country,
    city, landingPage, sessionCampaignName, sessionGoogleAdsKeyword, pagePath, date

    Common metrics: sessions, totalUsers, newUsers, bounceRate, conversions,
    totalRevenue, engagementRate, screenPageViews, averageSessionDuration

    Date range examples: "30daysAgo", "7daysAgo", "today", "yesterday", "2024-01-01"

    Args:
        property_id: GA4 numeric property ID (e.g. "123456789")
        dimensions: List of dimension names
        metrics: List of metric names
        start_date: Start date (e.g. "30daysAgo" or "YYYY-MM-DD")
        end_date: End date (e.g. "today" or "YYYY-MM-DD")
        limit: Maximum rows to return (default 100)
    """
    try:
        from .ga4 import run_report
        data = run_report(_ga4_client(), property_id, dimensions, metrics, start_date, end_date, limit)
        if not data:
            return f"No data returned for property {property_id} in the selected date range."
        headers = list(data[0].keys())
        rows = [[str(r.get(h, "")) for h in headers] for r in data]
        table = _table(headers, rows)
        return (
            f"**GA4 report — {start_date} to {end_date} (property {property_id})**\n\n"
            f"{table}"
        )
    except Exception as exc:
        return _err(str(exc))


@mcp.tool()
def get_realtime_users(
    property_id: str,
    dimensions: Optional[List[str]] = None,
) -> str:
    """Get real-time active user count from Google Analytics 4.

    Useful for verifying that a newly activated campaign is generating traffic,
    or monitoring live user activity.

    Args:
        property_id: GA4 numeric property ID
        dimensions: Optional breakdown dimensions (default: ["country"])
    """
    try:
        from .ga4 import run_realtime
        data = run_realtime(_ga4_client(), property_id, dimensions)
        if not data:
            return f"No active users right now on property {property_id}."
        total = sum(int(r["activeUsers"]) for r in data)
        headers = list(data[0].keys())
        rows = [[str(r.get(h, "")) for h in headers] for r in data]
        table = _table(headers, rows)
        return f"**Real-time active users: {total} (property {property_id})**\n\n{table}"
    except Exception as exc:
        return _err(str(exc))


@mcp.tool()
def get_ga4_events(property_id: str) -> str:
    """List all GA4 event names and their 30-day count.

    Use this to verify that conversion events are firing, check which events
    are tracked, and cross-reference with Google Ads conversion actions.

    Args:
        property_id: GA4 numeric property ID
    """
    try:
        from .ga4 import get_events
        data = get_events(_ga4_client(), property_id)
        if not data:
            return f"No events found for property {property_id} in the last 30 days."
        rows = [[r["eventName"], f"{r['eventCount']:,}"] for r in data]
        table = _table(["Event Name", "Count (30d)"], rows)
        return f"**GA4 events — last 30 days (property {property_id})**\n\n{table}"
    except Exception as exc:
        return _err(str(exc))


# ── Google Ads — Write tools (preview → confirm) ──────────────────────────────

@mcp.tool()
def preview_campaign_status_change(
    customer_id: str,
    campaign_id: str,
    action: str,
) -> str:
    """Preview pausing, enabling, or removing a campaign. Returns a plan_id to use with apply_change.

    ALWAYS call this before apply_change. Show the preview to the user and ask
    for explicit confirmation before proceeding.

    Args:
        customer_id: Google Ads account ID
        campaign_id: Numeric campaign ID
        action: One of "pause", "enable", or "remove"
    """
    if action not in ("pause", "enable", "remove"):
        return _err("action must be 'pause', 'enable', or 'remove'.")
    try:
        check_operation_allowed(action, _cfg().safety)
    except SafetyError as exc:
        return _err(str(exc))

    status = {"pause": "PAUSED", "enable": "ENABLED", "remove": "REMOVED"}[action]
    description = f"Set campaign {campaign_id} to {status} in account {customer_id}"
    plan = create_plan(
        operation=f"campaign_{action}",
        description=description,
        params={"customer_id": customer_id, "campaign_id": campaign_id, "status": status},
    )
    return (
        f"**Preview — {action.upper()} campaign**\n\n"
        f"| Field | Value |\n|-------|-------|\n"
        f"| Account | {customer_id} |\n"
        f"| Campaign ID | {campaign_id} |\n"
        f"| Change | → {status} |\n"
        f"| Plan ID | `{plan.id}` |\n\n"
        f"To apply this change, ask the user to confirm, then call `apply_change` "
        f"with `plan_id=\"{plan.id}\"` and `dry_run=False`."
    )


@mcp.tool()
def preview_add_negative_keywords(
    customer_id: str,
    keywords: List[str],
    match_type: str = "BROAD",
    campaign_id: Optional[str] = None,
    ad_group_id: Optional[str] = None,
) -> str:
    """Preview adding negative keywords to a campaign or ad group.

    ALWAYS call this before apply_change. Either campaign_id or ad_group_id is required.

    Args:
        customer_id: Google Ads account ID
        keywords: List of keyword texts to add as negatives
        match_type: "BROAD", "PHRASE", or "EXACT" (default: BROAD)
        campaign_id: Campaign ID (for campaign-level negatives)
        ad_group_id: Ad Group ID (for ad group-level negatives)
    """
    if not campaign_id and not ad_group_id:
        return _err("Provide either campaign_id or ad_group_id.")
    if match_type not in ("BROAD", "PHRASE", "EXACT"):
        return _err("match_type must be BROAD, PHRASE, or EXACT.")

    level = f"campaign {campaign_id}" if campaign_id else f"ad group {ad_group_id}"
    kw_list = [{"text": kw, "match_type": match_type} for kw in keywords]
    kw_preview = "\n".join(f"  - [{match_type}] {kw}" for kw in keywords)
    plan = create_plan(
        operation="add_negative_keywords",
        description=f"Add {len(keywords)} negative keyword(s) to {level}",
        params={
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "ad_group_id": ad_group_id,
            "keywords": kw_list,
        },
    )
    return (
        f"**Preview — Add negative keywords**\n\n"
        f"Account: {customer_id}\n"
        f"Target: {level}\n"
        f"Keywords to add:\n{kw_preview}\n\n"
        f"Plan ID: `{plan.id}`\n\n"
        f"Confirm with the user, then call `apply_change(plan_id=\"{plan.id}\", dry_run=False)`."
    )


@mcp.tool()
def preview_responsive_search_ad(
    customer_id: str,
    ad_group_id: str,
    final_url: str,
    headlines: List[str],
    descriptions: List[str],
    path1: str = "",
    path2: str = "",
) -> str:
    """Preview creating a Responsive Search Ad. Returns a plan_id to use with apply_change.

    Validates headline/description counts and character limits before previewing.
    New ads are always created in PAUSED status.

    Args:
        customer_id: Google Ads account ID
        ad_group_id: Ad group ID where the ad will be created
        final_url: Landing page URL (must include https://)
        headlines: 3–15 headlines, each max 30 characters
        descriptions: 2–4 descriptions, each max 90 characters
        path1: Optional URL path 1, max 15 characters
        path2: Optional URL path 2, max 15 characters
    """
    errors = []
    if len(headlines) < 3:
        errors.append(f"Need at least 3 headlines (got {len(headlines)}).")
    if len(headlines) > 15:
        errors.append(f"Maximum 15 headlines (got {len(headlines)}).")
    if len(descriptions) < 2:
        errors.append(f"Need at least 2 descriptions (got {len(descriptions)}).")
    if len(descriptions) > 4:
        errors.append(f"Maximum 4 descriptions (got {len(descriptions)}).")
    long_hl = [h for h in headlines if len(h) > 30]
    if long_hl:
        errors.append(f"Headlines over 30 chars: {long_hl}")
    long_desc = [d for d in descriptions if len(d) > 90]
    if long_desc:
        errors.append(f"Descriptions over 90 chars: {long_desc}")
    if not final_url.startswith("https://"):
        errors.append("final_url must start with https://")

    if errors:
        return _err("\n".join(errors))

    hl_preview = "\n".join(f"  H{i+1} ({len(h)} chars): {h}" for i, h in enumerate(headlines))
    desc_preview = "\n".join(f"  D{i+1} ({len(d)} chars): {d}" for i, d in enumerate(descriptions))
    plan = create_plan(
        operation="create_rsa",
        description=f"Create RSA in ad group {ad_group_id}",
        params={
            "customer_id": customer_id,
            "ad_group_id": ad_group_id,
            "headlines": headlines,
            "descriptions": descriptions,
            "final_url": final_url,
            "path1": path1,
            "path2": path2,
        },
    )
    return (
        f"**Preview — Create Responsive Search Ad (PAUSED)**\n\n"
        f"Account: {customer_id} | Ad Group: {ad_group_id}\n"
        f"URL: {final_url}"
        + (f" / {path1}" if path1 else "")
        + (f" / {path2}" if path2 else "")
        + f"\n\nHeadlines:\n{hl_preview}\n\nDescriptions:\n{desc_preview}\n\n"
        f"Plan ID: `{plan.id}`\n\n"
        f"Confirm with the user, then call `apply_change(plan_id=\"{plan.id}\", dry_run=False)`."
    )


@mcp.tool()
def apply_change(plan_id: str, dry_run: bool = True) -> str:
    """Execute a previously previewed change.

    ALWAYS show the preview to the user and get explicit confirmation before
    calling this with dry_run=False. When dry_run=True (default), it simulates
    the change without modifying Google Ads.

    Args:
        plan_id: The plan ID returned by a preview_* tool
        dry_run: True = simulate only (safe), False = apply real change (irreversible)
    """
    plan = get_plan(plan_id) if dry_run else consume_plan(plan_id)
    if not plan:
        return _err(
            f"Plan `{plan_id}` not found. It may have already been applied or expired. "
            f"Call the preview_* tool again to create a new plan."
        )

    cfg = _cfg()
    params = plan.params

    try:
        if plan.operation in ("campaign_pause", "campaign_enable", "campaign_remove"):
            from .ads import set_campaign_status
            result = set_campaign_status(
                _ads_client(),
                params["customer_id"],
                params["campaign_id"],
                params["status"],
                dry_run=dry_run,
            )
        elif plan.operation == "add_negative_keywords":
            from .ads import add_negative_keywords
            result = add_negative_keywords(
                _ads_client(),
                params["customer_id"],
                params.get("campaign_id"),
                params.get("ad_group_id"),
                params["keywords"],
                dry_run=dry_run,
            )
        elif plan.operation == "create_rsa":
            from .ads import create_responsive_search_ad
            result = create_responsive_search_ad(
                _ads_client(),
                params["customer_id"],
                params["ad_group_id"],
                params["headlines"],
                params["descriptions"],
                params["final_url"],
                params.get("path1", ""),
                params.get("path2", ""),
                dry_run=dry_run,
            )
        else:
            return _err(f"Unknown operation: {plan.operation}")
    except Exception as exc:
        return _err(str(exc))

    audit_log(
        cfg.safety.audit_log_path,
        plan.operation,
        plan.description,
        result,
        dry_run,
    )

    mode = "**[DRY-RUN]** Simulation successful." if dry_run else "**Change applied successfully.**"
    next_step = (
        f"\n\nTo apply for real, call `apply_change(plan_id=\"{plan_id}\", dry_run=False)`."
        if dry_run
        else "\n\nChange logged to audit log."
    )
    return f"{mode}\n\n{result}{next_step}"
