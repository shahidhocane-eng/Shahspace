#!/usr/bin/env python3
"""
CLI tool: verify a Shopify Storefront API connection and print shop status.

Usage:
  python storefront_connect.py

Requires SHOPIFY_STORE_DOMAIN and SHOPIFY_STOREFRONT_ACCESS_TOKEN to be
set in the environment (e.g. via a local .env file, see .env.example).
"""

import sys

from shopify import StorefrontClient, StorefrontAPIError


def main():
    client = StorefrontClient()

    try:
        shop = client.shop_info()
    except EnvironmentError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except StorefrontAPIError as exc:
        print(f"[ERROR] Could not reach Shopify Storefront API: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Connected to: {shop['name']}")
    print(f"  Storefront URL : {shop['primaryDomain']['url']}")

    try:
        products = client.products(first=5)
    except StorefrontAPIError as exc:
        print(f"[ERROR] Could not list products: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nProducts (up to 5):")
    for p in products:
        print(f"  {p['handle']:<30}  {p['title']}")
    if not products:
        print("  (none)")

    print("\nConnection successful.")


if __name__ == "__main__":
    main()
