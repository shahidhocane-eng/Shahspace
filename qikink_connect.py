#!/usr/bin/env python3
"""
CLI tool: verify a Qikink API connection by exchanging credentials for an
access token.

Usage:
  python qikink_connect.py

Requires QIKINK_CLIENT_ID and QIKINK_CLIENT_SECRET to be set in the
environment (e.g. via a local .env file, see .env.example). Defaults to
the sandbox environment; set QIKINK_ENV=live to hit production.
"""

import sys

from qikink import QikinkClient, QikinkAPIError


def main():
    client = QikinkClient()

    try:
        token = client.authenticate()
    except EnvironmentError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except QikinkAPIError as exc:
        print(f"[ERROR] Could not authenticate with Qikink: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Connected to Qikink ({client.env}): {client.base_url}")
    print(f"  Access token: {token[:8]}... (truncated)")
    print(
        "\nToken auth succeeded. Order/product endpoint paths and payloads "
        "aren't verified by this client — check your Qikink Postman "
        "collection, then call client.request(method, path, json=...) to use them."
    )


if __name__ == "__main__":
    main()
