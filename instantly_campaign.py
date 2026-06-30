#!/usr/bin/env python3
"""
CLI tool: manage Instantly.ai outreach campaigns.

Requires INSTANTLY_API_KEY to be set in the environment.

Subcommands:
  list                     List campaigns
  show  <campaign_id>      Show campaign details + analytics
  create                   Create a new campaign (interactive prompts)
  leads <campaign_id>      List leads for a campaign
  analytics <id> [<id>…]  Print analytics for one or more campaigns
"""

import argparse
import json
import sys

from instantly import InstantlyClient, add_leads, create_campaign, get_analytics
from instantly import get_campaign_summary, list_campaigns


def _client() -> InstantlyClient:
    try:
        return InstantlyClient()
    except EnvironmentError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    client = _client()
    campaigns = list_campaigns(client, limit=args.limit)
    if not campaigns:
        print("No campaigns found.")
        return
    for c in campaigns:
        status = c.get("status", "unknown")
        print(f"  {c.get('id', '?'):36s}  [{status:12s}]  {c.get('name', '')}")


def cmd_show(args):
    client = _client()
    summary = get_campaign_summary(client, args.campaign_id)
    print(json.dumps(summary, indent=2))


def cmd_create(args):
    name = args.name or input("Campaign name: ").strip()
    subject = args.subject or input("Email subject: ").strip()
    body = args.body or input("Email body (single line): ").strip()

    client = _client()
    result = create_campaign(client, name=name, subject=subject, body=body)
    print("Campaign created:")
    print(json.dumps(result, indent=2))


def cmd_leads(args):
    client = _client()
    result = client.list_leads(args.campaign_id, limit=args.limit)
    items = result.get("items", result) if isinstance(result, dict) else result
    if not items:
        print("No leads found.")
        return
    for lead in items:
        print(f"  {lead.get('id', '?'):36s}  {lead.get('email', '')}")


def cmd_analytics(args):
    client = _client()
    result = get_analytics(client, args.campaign_ids)
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Manage Instantly.ai campaigns from the command line.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List campaigns")
    p_list.add_argument("--limit", type=int, default=20, help="Max results (default 20)")
    p_list.set_defaults(func=cmd_list)

    # show
    p_show = sub.add_parser("show", help="Show campaign details + analytics")
    p_show.add_argument("campaign_id", help="Campaign ID")
    p_show.set_defaults(func=cmd_show)

    # create
    p_create = sub.add_parser("create", help="Create a campaign")
    p_create.add_argument("--name", default="", help="Campaign name")
    p_create.add_argument("--subject", default="", help="Email subject")
    p_create.add_argument("--body", default="", help="Email body text")
    p_create.set_defaults(func=cmd_create)

    # leads
    p_leads = sub.add_parser("leads", help="List leads for a campaign")
    p_leads.add_argument("campaign_id", help="Campaign ID")
    p_leads.add_argument("--limit", type=int, default=20, help="Max results (default 20)")
    p_leads.set_defaults(func=cmd_leads)

    # analytics
    p_analytics = sub.add_parser("analytics", help="Print analytics for campaigns")
    p_analytics.add_argument("campaign_ids", nargs="+", help="One or more campaign IDs")
    p_analytics.set_defaults(func=cmd_analytics)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
