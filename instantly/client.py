"""
Instantly.ai REST API v2 client.

Reads INSTANTLY_API_KEY from the environment. Every public method returns
parsed JSON; HTTPError is raised on non-2xx responses.
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import json

_BASE_URL = "https://api.instantly.ai/api/v2"


class InstantlyClient:
    """Thin wrapper around the Instantly.ai REST API v2."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("INSTANTLY_API_KEY")
        if not self.api_key:
            raise EnvironmentError(
                "Instantly.ai API key not found. "
                "Set the INSTANTLY_API_KEY environment variable or pass api_key= explicitly."
            )

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Any:
        url = f"{_BASE_URL}{path}"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{qs}"

        data = json.dumps(body).encode() if body is not None else None
        req = Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")

        with urlopen(req) as resp:
            return json.loads(resp.read().decode())

    # ------------------------------------------------------------------ #
    # Campaigns
    # ------------------------------------------------------------------ #

    def list_campaigns(self, limit: int = 10, skip: int = 0) -> dict:
        return self._request("GET", "/campaigns", params={"limit": limit, "skip": skip})

    def get_campaign(self, campaign_id: str) -> dict:
        return self._request("GET", f"/campaigns/{campaign_id}")

    def create_campaign(self, payload: dict) -> dict:
        return self._request("POST", "/campaigns", body=payload)

    def update_campaign(self, campaign_id: str, payload: dict) -> dict:
        return self._request("PATCH", f"/campaigns/{campaign_id}", body=payload)

    # ------------------------------------------------------------------ #
    # Leads
    # ------------------------------------------------------------------ #

    def add_leads(self, payload: dict) -> dict:
        return self._request("POST", "/leads", body=payload)

    def list_leads(self, campaign_id: str, limit: int = 10, skip: int = 0) -> dict:
        return self._request(
            "GET",
            "/leads",
            params={"campaign_id": campaign_id, "limit": limit, "skip": skip},
        )

    def get_lead(self, lead_id: str) -> dict:
        return self._request("GET", f"/leads/{lead_id}")

    def delete_lead(self, lead_id: str, campaign_id: Optional[str] = None) -> dict:
        body = {}
        if campaign_id:
            body["campaign_id"] = campaign_id
        return self._request("DELETE", f"/leads/{lead_id}", body=body or None)

    # ------------------------------------------------------------------ #
    # Analytics
    # ------------------------------------------------------------------ #

    def get_campaign_analytics(
        self,
        campaign_ids: list[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {"campaign_ids": campaign_ids}
        if start_date:
            body["start_date"] = start_date
        if end_date:
            body["end_date"] = end_date
        return self._request("POST", "/analytics/campaign/summary", body=body)

    # ------------------------------------------------------------------ #
    # Sending accounts
    # ------------------------------------------------------------------ #

    def list_accounts(self, limit: int = 10, skip: int = 0) -> dict:
        return self._request("GET", "/accounts", params={"limit": limit, "skip": skip})

    # ------------------------------------------------------------------ #
    # Emails
    # ------------------------------------------------------------------ #

    def list_emails(
        self,
        campaign_id: Optional[str] = None,
        limit: int = 10,
        skip: int = 0,
    ) -> dict:
        params: dict[str, Any] = {"limit": limit, "skip": skip}
        if campaign_id:
            params["campaign_id"] = campaign_id
        return self._request("GET", "/emails", params=params)
