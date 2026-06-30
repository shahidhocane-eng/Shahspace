"""
Higher-level helpers built on top of InstantlyClient.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .client import InstantlyClient


def list_campaigns(client: "InstantlyClient", limit: int = 10) -> list[dict]:
    """Return a list of campaign dicts."""
    result = client.list_campaigns(limit=limit)
    return result.get("items", result) if isinstance(result, dict) else result


def get_campaign_summary(client: "InstantlyClient", campaign_id: str) -> dict:
    """Return campaign details plus a flattened analytics snapshot."""
    campaign = client.get_campaign(campaign_id)
    try:
        analytics = client.get_campaign_analytics([campaign_id])
        stats = analytics.get("data", {}).get(campaign_id, {})
    except Exception:
        stats = {}
    return {**campaign, "analytics": stats}


def create_campaign(
    client: "InstantlyClient",
    name: str,
    subject: str,
    body: str,
    from_name: Optional[str] = None,
    email_list: Optional[list[str]] = None,
    daily_limit: int = 50,
) -> dict:
    """
    Create a basic outreach campaign.

    Args:
        client: Authenticated InstantlyClient.
        name: Internal campaign name.
        subject: Email subject line.
        body: Plain-text email body.
        from_name: Sender display name (optional).
        email_list: Sending account emails to attach (optional).
        daily_limit: Max emails per day per sending account.

    Returns:
        The created campaign dict returned by the API.
    """
    payload: dict = {
        "name": name,
        "campaign_schedule": {"schedules": []},
        "sequences": [
            {
                "steps": [
                    {
                        "type": "email",
                        "delay": 0,
                        "variants": [
                            {
                                "subject": subject,
                                "body": body,
                            }
                        ],
                    }
                ]
            }
        ],
        "daily_limit": daily_limit,
    }
    if from_name:
        payload["from_name"] = from_name
    if email_list:
        payload["email_list"] = email_list

    return client.create_campaign(payload)


def add_leads(
    client: "InstantlyClient",
    campaign_id: str,
    leads: list[dict],
) -> dict:
    """
    Add leads to a campaign.

    Each lead dict must have at least {"email": "..."}.  Optional fields
    include first_name, last_name, company_name, custom_variables, etc.

    Returns:
        The API response (total_count, new_count, duplicate_count, etc.).
    """
    payload = {"campaign_id": campaign_id, "leads": leads}
    return client.add_leads(payload)


def get_analytics(
    client: "InstantlyClient",
    campaign_ids: list[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Return analytics data for one or more campaigns."""
    return client.get_campaign_analytics(
        campaign_ids, start_date=start_date, end_date=end_date
    )
