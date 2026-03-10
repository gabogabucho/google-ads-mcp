"""Google OAuth 2.0 authentication with token caching.

Supports:
  - Service account JSON (auto-detected)
  - OAuth 2.0 desktop flow (interactive, cached)
  - Application Default Credentials (fallback)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Unified scopes for both Google Ads and GA4
SCOPES = [
    "https://www.googleapis.com/auth/adwords",
    "https://www.googleapis.com/auth/analytics.readonly",
]


def get_credentials(
    credentials_path: str,
    token_path: str,
) -> Credentials:
    """Return valid Google credentials, refreshing or re-authenticating as needed."""
    creds_path = Path(credentials_path)
    token_path_ = Path(token_path)

    # 1. Service account
    if creds_path.exists():
        raw = json.loads(creds_path.read_text(encoding="utf-8"))
        if raw.get("type") == "service_account":
            return service_account.Credentials.from_service_account_file(
                str(creds_path), scopes=SCOPES
            )

    # 2. Cached OAuth token
    creds: Optional[Credentials] = None
    if token_path_.exists():
        creds = Credentials.from_authorized_user_file(str(token_path_), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_token(creds, token_path_)
        return creds

    # 3. Interactive OAuth flow
    if not creds_path.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {creds_path}\n"
            "Download OAuth 2.0 credentials from Google Cloud Console:\n"
            "  APIs & Services → Credentials → Create → OAuth 2.0 Client ID → Desktop app"
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(port=0)
    _save_token(creds, token_path_)
    return creds


def _save_token(creds: Credentials, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json(), encoding="utf-8")
