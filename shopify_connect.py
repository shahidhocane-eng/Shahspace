#!/usr/bin/env python3
"""
CLI tool: verify a Shopify Admin API connection and print shop status.

Usage:
  python shopify_connect.py

Requires SHOPIFY_STORE_DOMAIN and SHOPIFY_ACCESS_TOKEN to be set in the
environment (e.g. via a local .env file, see .env.example).
"""

import sys

from shopify import ShopifyClient, ShopifyAPIError


def main():
    client = ShopifyClient()

    try:
        shop = client.shop()
    except EnvironmentError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except ShopifyAPIError as exc:
        print(f"[ERROR] Could not reach Shopify API: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Connected to: {shop['name']} ({shop['myshopify_domain']})")
    print(f"  Plan     : {shop.get('plan_display_name', 'n/a')}")
    print(f"  Currency : {shop.get('currency', 'n/a')}")
    print(f"  Timezone : {shop.get('iana_timezone', 'n/a')}")

    try:
        products = client.products(limit=5)
    except ShopifyAPIError as exc:
        print(f"[ERROR] Could not list products: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nProducts (up to 5):")
    for p in products:
        print(f"  {p['id']:>12}  {p['title']}")
    if not products:
        print("  (none)")

    print("\nConnection successful.")


if __name__ == "__main__":
    main()
