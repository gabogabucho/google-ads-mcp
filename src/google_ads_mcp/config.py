"""Configuration loader for google-ads-mcp.

Config file location (in order of priority):
  1. GOOGLE_ADS_MCP_CONFIG environment variable
  2. ~/.google-ads-mcp/config.yaml  (all platforms)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

# Cross-platform default config directory
CONFIG_DIR = Path.home() / ".google-ads-mcp"


@dataclass
class GoogleConfig:
    """Google Cloud / OAuth settings."""
    credentials_path: str = str(CONFIG_DIR / "credentials.json")
    token_path: str = str(CONFIG_DIR / "token.json")


@dataclass
class AdsConfig:
    """Google Ads API settings."""
    developer_token: str = ""
    customer_id: str = ""
    login_customer_id: Optional[str] = None


@dataclass
class GA4Config:
    """Google Analytics 4 settings."""
    property_id: str = ""


@dataclass
class SafetyConfig:
    """Safety limits for write operations."""
    max_daily_budget_usd: float = 100.0
    max_bid_increase_pct: int = 50
    require_preview: bool = True
    audit_log_path: str = str(CONFIG_DIR / "audit.log")
    blocked_operations: List[str] = field(default_factory=list)


@dataclass
class Config:
    google: GoogleConfig = field(default_factory=GoogleConfig)
    ads: AdsConfig = field(default_factory=AdsConfig)
    ga4: GA4Config = field(default_factory=GA4Config)
    safety: SafetyConfig = field(default_factory=SafetyConfig)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        config_path = _resolve_config_path(path)
        if not config_path.exists():
            raise FileNotFoundError(
                f"Config not found: {config_path}\n"
                f"Create it from the example in config/config.yaml.example\n"
                f"Then fill in your Google Ads developer token and credentials path."
            )
        with open(config_path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

        return cls(
            google=GoogleConfig(**_expand_paths(raw.get("google", {}))),
            ads=AdsConfig(**raw.get("ads", {})),
            ga4=GA4Config(**raw.get("ga4", {})),
            safety=SafetyConfig(**raw.get("safety", {})),
        )


# ── helpers ──────────────────────────────────────────────────────────────────

def _resolve_config_path(override: Optional[str]) -> Path:
    if override:
        return Path(override).expanduser()
    env = os.environ.get("GOOGLE_ADS_MCP_CONFIG")
    if env:
        return Path(env).expanduser()
    return CONFIG_DIR / "config.yaml"


def _expand_paths(mapping: dict) -> dict:
    """Expand ~ in path-like string values."""
    out = {}
    for k, v in mapping.items():
        if isinstance(v, str) and ("/" in v or "\\" in v or v.startswith("~")):
            out[k] = str(Path(v).expanduser())
        else:
            out[k] = v
    return out
