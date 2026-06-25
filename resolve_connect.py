#!/usr/bin/env python3
"""
CLI tool: verify and inspect a DaVinci Resolve connection.

Usage:
  python resolve_connect.py              # connect to local Resolve
  python resolve_connect.py --host IP   # connect to remote Resolve
"""

import argparse
import sys
from davinci_resolve import connect, get_project_info, get_resolve_version, list_timelines


def main():
    parser = argparse.ArgumentParser(description="Connect to DaVinci Resolve and print status.")
    parser.add_argument("--host", default=None, help="IP of remote Resolve machine (default: local)")
    args = parser.parse_args()

    print(f"Connecting to DaVinci Resolve{f' at {args.host}' if args.host else ' (local)'}...")

    try:
        conn = connect(host=args.host)
    except EnvironmentError as exc:
        print(f"[ERROR] Scripting module not found:\n  {exc}", file=sys.stderr)
        sys.exit(1)
    except ConnectionError as exc:
        print(f"[ERROR] Could not connect:\n  {exc}", file=sys.stderr)
        sys.exit(1)

    version = get_resolve_version(conn)
    print(f"  Resolve version : {version}")

    info = get_project_info(conn)
    if info:
        print(f"  Project         : {info['name']}")
        print(f"  Resolution      : {info['width']}x{info['height']} @ {info['frame_rate']} fps")
        timelines = list_timelines(conn)
        print(f"  Timelines ({len(timelines)})  : {', '.join(timelines) or 'none'}")
        if conn.timeline:
            print(f"  Active timeline : {conn.timeline.GetName()}")
    else:
        print("  No project currently open in Resolve.")

    print("\nConnection successful.")


if __name__ == "__main__":
    main()
