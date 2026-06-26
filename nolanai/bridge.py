"""
Bridge between a live DaVinci Resolve connection and Nolan AI Studio.

Typical usage::

    from davinci_resolve import connect
    from nolanai import NolanAIClient
    from nolanai.bridge import push_resolve_project, pull_nolan_project

    conn   = connect()
    client = NolanAIClient()

    nolan_project = push_resolve_project(conn, client)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from davinci_resolve.connect import ResolveConnection
    from nolanai.client import NolanAIClient


def push_resolve_project(
    conn: "ResolveConnection",
    client: "NolanAIClient",
    project_id: str | None = None,
) -> dict:
    """
    Push the currently open DaVinci Resolve project (and all its timelines)
    to Nolan AI Studio.

    If *project_id* is given the data is merged into that existing Nolan AI
    project; otherwise a new project is created.

    Returns the Nolan AI project dict.
    """
    from davinci_resolve.utils import get_project_info, list_timelines

    info = get_project_info(conn)
    if not info:
        raise RuntimeError("No project is currently open in DaVinci Resolve.")

    resolve_name = info["name"]

    if project_id:
        nolan_project = client.get_project(project_id)
    else:
        nolan_project = client.create_project(
            name=resolve_name,
            description=f"Imported from DaVinci Resolve — {resolve_name}",
        )
        project_id = nolan_project.get("id") or nolan_project.get("project", {}).get("id")

    # Push each timeline as a sequence
    for tl_name in list_timelines(conn):
        client.push_sequence(
            project_id=project_id,
            name=tl_name,
            metadata={
                "source": "davinci_resolve",
                "resolve_project": resolve_name,
                "frame_rate": info.get("frame_rate"),
                "width": info.get("width"),
                "height": info.get("height"),
            },
        )

    return nolan_project


def pull_nolan_project(client: "NolanAIClient", project_id: str) -> dict:
    """
    Fetch a Nolan AI Studio project and return a summary dict containing
    the project metadata and its sequences/assets — useful for display or
    further processing inside DaVinci Resolve.
    """
    project = client.get_project(project_id)
    sequences = client.list_sequences(project_id)
    assets = client.list_assets(project_id)
    return {
        "project": project,
        "sequences": sequences,
        "assets": assets,
    }
