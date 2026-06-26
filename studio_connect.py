#!/usr/bin/env python3
"""
CLI tool: connect DaVinci Resolve to the Nolan AI Studio dashboard.

Usage:
  # Verify credentials and list Nolan AI Studio projects
  python studio_connect.py status

  # Push the currently open Resolve project to a new Nolan AI Studio project
  python studio_connect.py push

  # Push into an existing Nolan AI Studio project
  python studio_connect.py push --project-id <id>

  # Pull and display a Nolan AI Studio project
  python studio_connect.py pull --project-id <id>

  # List all projects in the Nolan AI Studio account
  python studio_connect.py list

Environment variables:
  NOLANAI_API_KEY   Nolan AI Studio API key  (required)
  RESOLVE_HOST      IP of a remote DaVinci Resolve machine (optional)
"""

import argparse
import json
import os
import sys

from nolanai import NolanAIClient, NolanAIError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client() -> NolanAIClient:
    try:
        return NolanAIClient()
    except NolanAIError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


def _resolve_conn():
    """Return a ResolveConnection, or None if Resolve is not available."""
    try:
        from davinci_resolve import connect
        host = os.environ.get("RESOLVE_HOST")
        return connect(host=host)
    except EnvironmentError as exc:
        print(f"[WARN] DaVinci Resolve scripting module not found: {exc}", file=sys.stderr)
        return None
    except ConnectionError as exc:
        print(f"[WARN] Could not connect to DaVinci Resolve: {exc}", file=sys.stderr)
        return None


def _print_json(data):
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def cmd_status(args):
    """Verify Nolan AI Studio credentials and (optionally) Resolve connectivity."""
    client = _make_client()

    print(f"Connecting to Nolan AI Studio at https://studio.nolanai.app ...")
    try:
        me = client.ping()
        name = me.get("name") or me.get("user", {}).get("name") or "(unknown)"
        email = me.get("email") or me.get("user", {}).get("email") or ""
        print(f"  Authenticated as : {name} {f'<{email}>' if email else ''}")
    except NolanAIError as exc:
        print(f"[ERROR] Nolan AI Studio: {exc}", file=sys.stderr)
        sys.exit(1)

    conn = _resolve_conn()
    if conn:
        from davinci_resolve.utils import get_resolve_version, get_project_info
        version = get_resolve_version(conn)
        info = get_project_info(conn)
        print(f"  DaVinci Resolve  : v{version}")
        if info:
            print(f"  Open project     : {info['name']} ({info['width']}x{info['height']} @ {info['frame_rate']} fps)")
        else:
            print("  Open project     : (none)")
    else:
        print("  DaVinci Resolve  : not connected")

    print("\nStatus check complete.")


def cmd_list(args):
    """List all projects in the Nolan AI Studio account."""
    client = _make_client()
    try:
        projects = client.list_projects()
    except NolanAIError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    if not projects:
        print("No projects found in Nolan AI Studio.")
        return

    print(f"{'ID':<36}  Name")
    print("-" * 60)
    for p in projects:
        pid = p.get("id", "?")
        pname = p.get("name", "(unnamed)")
        print(f"{pid:<36}  {pname}")


def cmd_push(args):
    """Push the open DaVinci Resolve project to Nolan AI Studio."""
    client = _make_client()
    conn = _resolve_conn()

    if conn is None:
        print("[ERROR] DaVinci Resolve is not available — cannot push.", file=sys.stderr)
        sys.exit(1)

    from nolanai.bridge import push_resolve_project
    print("Pushing DaVinci Resolve project to Nolan AI Studio ...")
    try:
        result = push_resolve_project(conn, client, project_id=args.project_id)
    except (NolanAIError, RuntimeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    pid = result.get("id") or result.get("project", {}).get("id") or "?"
    pname = result.get("name") or result.get("project", {}).get("name") or "?"
    print(f"  Nolan AI project : {pname}  (id: {pid})")
    print("\nPush complete.")


def cmd_pull(args):
    """Pull and display a Nolan AI Studio project."""
    if not args.project_id:
        print("[ERROR] --project-id is required for 'pull'.", file=sys.stderr)
        sys.exit(1)

    client = _make_client()
    from nolanai.bridge import pull_nolan_project
    try:
        data = pull_nolan_project(client, args.project_id)
    except NolanAIError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    _print_json(data)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Connect DaVinci Resolve to the Nolan AI Studio dashboard.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # status
    p_status = sub.add_parser("status", help="Check Nolan AI Studio auth and Resolve connectivity")
    p_status.set_defaults(func=cmd_status)

    # list
    p_list = sub.add_parser("list", help="List Nolan AI Studio projects")
    p_list.set_defaults(func=cmd_list)

    # push
    p_push = sub.add_parser("push", help="Push open Resolve project to Nolan AI Studio")
    p_push.add_argument("--project-id", default=None, help="Push into an existing Nolan AI project")
    p_push.set_defaults(func=cmd_push)

    # pull
    p_pull = sub.add_parser("pull", help="Pull a Nolan AI Studio project and display it")
    p_pull.add_argument("--project-id", required=True, help="Nolan AI Studio project ID")
    p_pull.set_defaults(func=cmd_pull)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
