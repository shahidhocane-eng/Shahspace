"""
Utility helpers built on top of ResolveConnection.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .connect import ResolveConnection


def get_project_info(conn: "ResolveConnection") -> dict:
    """Return basic info about the current project."""
    project = conn.project
    if not project:
        return {}
    return {
        "name": project.GetName(),
        "frame_rate": project.GetSetting("timelineFrameRate"),
        "width": project.GetSetting("timelineResolutionWidth"),
        "height": project.GetSetting("timelineResolutionHeight"),
    }


def list_timelines(conn: "ResolveConnection") -> list[str]:
    """Return the names of all timelines in the current project."""
    project = conn.project
    if not project:
        return []
    count = project.GetTimelineCount()
    return [project.GetTimelineByIndex(i + 1).GetName() for i in range(count)]


def switch_timeline(conn: "ResolveConnection", name: str) -> bool:
    """Switch to a timeline by name. Returns True on success."""
    project = conn.project
    if not project:
        return False
    count = project.GetTimelineCount()
    for i in range(count):
        tl = project.GetTimelineByIndex(i + 1)
        if tl.GetName() == name:
            project.SetCurrentTimeline(tl)
            conn.timeline = tl
            return True
    return False


def import_media(conn: "ResolveConnection", *file_paths: str) -> list:
    """
    Import media files into the current project's media pool.

    Args:
        conn: Active ResolveConnection.
        *file_paths: Absolute paths to media files.

    Returns:
        List of MediaPoolItem objects that were imported.
    """
    pool = conn.media_pool
    if not pool:
        raise RuntimeError("No project open — cannot import media.")

    abs_paths = [os.path.abspath(p) for p in file_paths]
    return pool.ImportMedia(abs_paths) or []


def export_timeline_xml(conn: "ResolveConnection", output_path: str) -> bool:
    """Export the current timeline as a DaVinci Resolve XML file."""
    timeline = conn.timeline
    if not timeline:
        raise RuntimeError("No timeline is currently active.")
    return timeline.Export(os.path.abspath(output_path), 0)  # 0 = DRT / Resolve XML


def get_resolve_version(conn: "ResolveConnection") -> str:
    """Return the DaVinci Resolve application version string."""
    info = conn.resolve.GetVersion()
    if isinstance(info, list):
        return ".".join(str(v) for v in info)
    return str(info)
