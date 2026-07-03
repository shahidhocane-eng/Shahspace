#!/usr/bin/env python3
"""
CLI tool: verify a WazirX API connection and print account status.

Usage:
  python wazirx_connect.py

Requires WAZIRX_API_KEY and WAZIRX_API_SECRET to be set in the
environment (e.g. via a local .env file, see .env.example).
"""

import sys

from wazirx import WazirxClient, WazirxAPIError


def main():
    client = WazirxClient()

    try:
        status = client.system_status()
        print(f"System status : {status.get('status', status)}")
    except WazirxAPIError as exc:
        print(f"[ERROR] Could not reach WazirX API: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        account = client.account()
    except EnvironmentError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except WazirxAPIError as exc:
        print(f"[ERROR] Authentication failed: {exc}", file=sys.stderr)
        sys.exit(1)

    balances = [b for b in account.get("balances", []) if float(b.get("free", 0)) or float(b.get("locked", 0))]
    print(f"\nConnected. Non-zero balances ({len(balances)}):")
    for b in balances:
        print(f"  {b['asset']:>6}  free={b['free']}  locked={b['locked']}")

    if not balances:
        print("  (none)")

    print("\nConnection successful.")


if __name__ == "__main__":
    main()
