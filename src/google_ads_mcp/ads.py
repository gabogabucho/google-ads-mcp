"""Google Ads API operations — read and write.

All monetary values from the API are in micros (1/1,000,000 of currency unit).
We convert to the base currency unit (e.g. USD) before returning.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from .config import AdsConfig
from .auth import get_credentials

_MICROS = 1_000_000


# ── Client factory ────────────────────────────────────────────────────────────

def make_ads_client(
    ads_cfg: AdsConfig,
    credentials_path: str,
    token_path: str,
) -> GoogleAdsClient:
    creds = get_credentials(credentials_path, token_path)
    config: Dict[str, Any] = {
        "developer_token": ads_cfg.developer_token,
        "use_proto_plus": True,
    }
    if ads_cfg.login_customer_id:
        config["login_customer_id"] = _clean_id(ads_cfg.login_customer_id)

    return GoogleAdsClient.load_from_dict(config, credentials=creds)


def _clean_id(customer_id: str) -> str:
    """Remove dashes from customer IDs (123-456-7890 → 1234567890)."""
    return customer_id.replace("-", "")


def _ga_service(client: GoogleAdsClient):
    return client.get_service("GoogleAdsService")


# ── Read operations ───────────────────────────────────────────────────────────

def list_accounts(client: GoogleAdsClient) -> List[Dict[str, str]]:
    """Return all accessible Google Ads accounts."""
    service = client.get_service("CustomerService")
    response = service.list_accessible_customers()
    accounts = []
    for resource_name in response.resource_names:
        cid = resource_name.split("/")[-1]
        accounts.append({"customer_id": cid, "resource_name": resource_name})
    return accounts


def get_campaign_performance(
    client: GoogleAdsClient,
    customer_id: str,
    start_date: str,
    end_date: str,
) -> List[Dict[str, Any]]:
    query = f"""
        SELECT
          campaign.id,
          campaign.name,
          campaign.status,
          campaign.advertising_channel_type,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value,
          metrics.ctr,
          metrics.average_cpc
        FROM campaign
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 100
    """
    rows = []
    for row in _ga_service(client).search(customer_id=_clean_id(customer_id), query=query):
        m = row.metrics
        rows.append({
            "campaign_id": row.campaign.id,
            "campaign_name": row.campaign.name,
            "status": row.campaign.status.name,
            "channel": row.campaign.advertising_channel_type.name,
            "impressions": m.impressions,
            "clicks": m.clicks,
            "cost_usd": m.cost_micros / _MICROS,
            "conversions": m.conversions,
            "conv_value": m.conversions_value,
            "ctr_pct": m.ctr * 100,
            "avg_cpc_usd": m.average_cpc / _MICROS,
        })
    return rows


def get_ad_performance(
    client: GoogleAdsClient,
    customer_id: str,
    start_date: str,
    end_date: str,
) -> List[Dict[str, Any]]:
    query = f"""
        SELECT
          ad_group_ad.ad.id,
          ad_group_ad.ad.type,
          ad_group_ad.status,
          ad_group_ad.ad.final_urls,
          campaign.name,
          ad_group.name,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.ctr
        FROM ad_group_ad
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
          AND ad_group_ad.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 100
    """
    rows = []
    for row in _ga_service(client).search(customer_id=_clean_id(customer_id), query=query):
        m = row.metrics
        ad = row.ad_group_ad.ad
        rows.append({
            "ad_id": ad.id,
            "ad_type": ad.type_.name,
            "status": row.ad_group_ad.status.name,
            "final_url": ad.final_urls[0] if ad.final_urls else "",
            "campaign": row.campaign.name,
            "ad_group": row.ad_group.name,
            "impressions": m.impressions,
            "clicks": m.clicks,
            "cost_usd": m.cost_micros / _MICROS,
            "conversions": m.conversions,
            "ctr_pct": m.ctr * 100,
        })
    return rows


def get_keyword_performance(
    client: GoogleAdsClient,
    customer_id: str,
    start_date: str,
    end_date: str,
) -> List[Dict[str, Any]]:
    query = f"""
        SELECT
          ad_group_criterion.criterion_id,
          ad_group_criterion.keyword.text,
          ad_group_criterion.keyword.match_type,
          ad_group_criterion.status,
          ad_group_criterion.quality_info.quality_score,
          ad_group_criterion.cpc_bid_micros,
          campaign.name,
          ad_group.name,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.ctr,
          metrics.average_cpc
        FROM keyword_view
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
          AND ad_group_criterion.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 200
    """
    rows = []
    for row in _ga_service(client).search(customer_id=_clean_id(customer_id), query=query):
        m = row.metrics
        kw = row.ad_group_criterion
        rows.append({
            "criterion_id": kw.criterion_id,
            "keyword": kw.keyword.text,
            "match_type": kw.keyword.match_type.name,
            "status": kw.status.name,
            "quality_score": kw.quality_info.quality_score,
            "bid_usd": kw.cpc_bid_micros / _MICROS,
            "campaign": row.campaign.name,
            "ad_group": row.ad_group.name,
            "impressions": m.impressions,
            "clicks": m.clicks,
            "cost_usd": m.cost_micros / _MICROS,
            "conversions": m.conversions,
            "ctr_pct": m.ctr * 100,
            "avg_cpc_usd": m.average_cpc / _MICROS,
        })
    return rows


def get_search_terms(
    client: GoogleAdsClient,
    customer_id: str,
    start_date: str,
    end_date: str,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    query = f"""
        SELECT
          search_term_view.search_term,
          search_term_view.status,
          campaign.name,
          ad_group.name,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.ctr
        FROM search_term_view
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY metrics.cost_micros DESC
        LIMIT {limit}
    """
    rows = []
    for row in _ga_service(client).search(customer_id=_clean_id(customer_id), query=query):
        m = row.metrics
        rows.append({
            "search_term": row.search_term_view.search_term,
            "status": row.search_term_view.status.name,
            "campaign": row.campaign.name,
            "ad_group": row.ad_group.name,
            "impressions": m.impressions,
            "clicks": m.clicks,
            "cost_usd": m.cost_micros / _MICROS,
            "conversions": m.conversions,
            "ctr_pct": m.ctr * 100,
        })
    return rows


def run_gaql(
    client: GoogleAdsClient,
    customer_id: str,
    query: str,
) -> List[Dict[str, Any]]:
    """Execute an arbitrary GAQL query and return rows as dicts."""
    rows = []
    for row in _ga_service(client).search(customer_id=_clean_id(customer_id), query=query):
        rows.append(_proto_to_dict(row))
    return rows


def _proto_to_dict(proto_obj: Any) -> Dict[str, Any]:
    """Shallow conversion of a proto-plus row to a plain dict."""
    try:
        from google.protobuf.json_format import MessageToDict
        return MessageToDict(proto_obj._pb, preserving_proto_field_name=True)
    except Exception:
        return {"raw": str(proto_obj)}


# ── Write operations ──────────────────────────────────────────────────────────

_STATUS_MAP = {
    "pause": "PAUSED",
    "enable": "ENABLED",
    "remove": "REMOVED",
}


def set_campaign_status(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str,
    status: str,
    dry_run: bool = True,
) -> str:
    """Pause, enable, or remove a campaign. Returns summary string."""
    cid = _clean_id(customer_id)
    service = client.get_service("CampaignService")
    resource = service.campaign_path(cid, campaign_id)

    if dry_run:
        return f"[DRY-RUN] Would set campaign {campaign_id} → {status}"

    campaign = client.get_type("Campaign")
    campaign.resource_name = resource
    campaign.status = getattr(client.enums.CampaignStatusEnum, status)

    op = client.get_type("CampaignOperation")
    op.update.CopyFrom(campaign)
    op.update_mask.paths.append("status")

    try:
        response = service.mutate_campaigns(customer_id=cid, operations=[op])
        return f"Campaign {campaign_id} status set to {status}. Resource: {response.results[0].resource_name}"
    except GoogleAdsException as ex:
        raise RuntimeError(_format_ads_error(ex)) from ex


def set_ad_group_status(
    client: GoogleAdsClient,
    customer_id: str,
    ad_group_id: str,
    status: str,
    dry_run: bool = True,
) -> str:
    cid = _clean_id(customer_id)
    service = client.get_service("AdGroupService")
    resource = service.ad_group_path(cid, ad_group_id)

    if dry_run:
        return f"[DRY-RUN] Would set ad group {ad_group_id} → {status}"

    ad_group = client.get_type("AdGroup")
    ad_group.resource_name = resource
    ad_group.status = getattr(client.enums.AdGroupStatusEnum, status)

    op = client.get_type("AdGroupOperation")
    op.update.CopyFrom(ad_group)
    op.update_mask.paths.append("status")

    try:
        response = service.mutate_ad_groups(customer_id=cid, operations=[op])
        return f"Ad group {ad_group_id} status set to {status}. Resource: {response.results[0].resource_name}"
    except GoogleAdsException as ex:
        raise RuntimeError(_format_ads_error(ex)) from ex


def add_negative_keywords(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: Optional[str],
    ad_group_id: Optional[str],
    keywords: List[Dict[str, str]],
    dry_run: bool = True,
) -> str:
    """Add negative keywords at campaign or ad group level."""
    cid = _clean_id(customer_id)
    level = "campaign" if campaign_id else "ad group"
    kw_list = [f"{k['text']} ({k.get('match_type', 'BROAD')})" for k in keywords]
    preview = "\n".join(f"  - {kw}" for kw in kw_list)

    if dry_run:
        return f"[DRY-RUN] Would add {len(keywords)} negative keyword(s) to {level}:\n{preview}"

    ops = []
    if campaign_id:
        campaign_resource = client.get_service("CampaignService").campaign_path(cid, campaign_id)
        for kw in keywords:
            criterion = client.get_type("CampaignCriterion")
            criterion.campaign = campaign_resource
            criterion.negative = True
            criterion.keyword.text = kw["text"]
            criterion.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum,
                kw.get("match_type", "BROAD"),
            )
            op = client.get_type("CampaignCriterionOperation")
            op.create.CopyFrom(criterion)
            ops.append(op)

        service = client.get_service("CampaignCriterionService")
        try:
            service.mutate_campaign_criteria(customer_id=cid, operations=ops)
        except GoogleAdsException as ex:
            raise RuntimeError(_format_ads_error(ex)) from ex
    else:
        ad_group_resource = client.get_service("AdGroupService").ad_group_path(cid, ad_group_id)
        for kw in keywords:
            criterion = client.get_type("AdGroupCriterion")
            criterion.ad_group = ad_group_resource
            criterion.negative = True
            criterion.keyword.text = kw["text"]
            criterion.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum,
                kw.get("match_type", "BROAD"),
            )
            op = client.get_type("AdGroupCriterionOperation")
            op.create.CopyFrom(criterion)
            ops.append(op)

        service = client.get_service("AdGroupCriterionService")
        try:
            service.mutate_ad_group_criteria(customer_id=cid, operations=ops)
        except GoogleAdsException as ex:
            raise RuntimeError(_format_ads_error(ex)) from ex

    return f"Added {len(keywords)} negative keyword(s) to {level}:\n{preview}"


def create_responsive_search_ad(
    client: GoogleAdsClient,
    customer_id: str,
    ad_group_id: str,
    headlines: List[str],
    descriptions: List[str],
    final_url: str,
    path1: str = "",
    path2: str = "",
    dry_run: bool = True,
) -> str:
    """Create a Responsive Search Ad. New ads are always created PAUSED."""
    cid = _clean_id(customer_id)
    hl_preview = "\n".join(f"  H{i+1}: {h}" for i, h in enumerate(headlines))
    desc_preview = "\n".join(f"  D{i+1}: {d}" for i, d in enumerate(descriptions))

    if dry_run:
        return (
            f"[DRY-RUN] Would create RSA in ad group {ad_group_id} (status: PAUSED)\n"
            f"URL: {final_url}\n"
            f"Headlines:\n{hl_preview}\n"
            f"Descriptions:\n{desc_preview}"
        )

    ad_group_resource = client.get_service("AdGroupService").ad_group_path(cid, ad_group_id)
    ad = client.get_type("Ad")
    ad.final_urls.append(final_url)
    if path1:
        ad.responsive_search_ad.path1 = path1
    if path2:
        ad.responsive_search_ad.path2 = path2
    for text in headlines:
        asset = client.get_type("AdTextAsset")
        asset.text = text
        ad.responsive_search_ad.headlines.append(asset)
    for text in descriptions:
        asset = client.get_type("AdTextAsset")
        asset.text = text
        ad.responsive_search_ad.descriptions.append(asset)

    ad_group_ad = client.get_type("AdGroupAd")
    ad_group_ad.ad_group = ad_group_resource
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED
    ad_group_ad.ad.CopyFrom(ad)

    op = client.get_type("AdGroupAdOperation")
    op.create.CopyFrom(ad_group_ad)

    service = client.get_service("AdGroupAdService")
    try:
        response = service.mutate_ad_group_ads(customer_id=cid, operations=[op])
        return (
            f"RSA created (PAUSED) in ad group {ad_group_id}.\n"
            f"Resource: {response.results[0].resource_name}\n"
            f"Use enable_entity to activate it after review."
        )
    except GoogleAdsException as ex:
        raise RuntimeError(_format_ads_error(ex)) from ex


# ── Error formatting ──────────────────────────────────────────────────────────

def _format_ads_error(ex: GoogleAdsException) -> str:
    messages = []
    for error in ex.failure.errors:
        messages.append(f"{error.error_code}: {error.message}")
    return "Google Ads API error:\n" + "\n".join(messages)
