"""
DaVinci Resolve scripting API connection manager.

DaVinci Resolve must be open and have scripting enabled:
  Preferences > General > Enable local scripting API
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Platform-specific paths to DaVinci Resolve scripting modules
_MODULE_PATHS = {
    "darwin": [
        "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
        os.path.expanduser("~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"),
    ],
    "win32": [
        r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules",
        r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.py",
    ],
    "linux": [
        "/opt/resolve/Developer/Scripting/Modules",
        "/home/resolve/Developer/Scripting/Modules",
    ],
}


def _add_resolve_to_path() -> Optional[str]:
    """Add the Resolve scripting module directory to sys.path. Returns the path found, or None."""
    platform = sys.platform if sys.platform != "linux2" else "linux"
    candidates = _MODULE_PATHS.get(platform, [])

    # Also respect RESOLVE_SCRIPT_API env var (Blackmagic's recommended override)
    env_path = os.environ.get("RESOLVE_SCRIPT_API")
    if env_path:
        candidates = [os.path.join(env_path, "Modules")] + candidates

    for path in candidates:
        if Path(path).is_dir() and path not in sys.path:
            sys.path.insert(0, path)
            return path

    return None


class ResolveConnection:
    """Holds live references to the DaVinci Resolve scripting objects."""

    def __init__(self, resolve, project_manager, project=None, timeline=None):
        self.resolve = resolve
        self.project_manager = project_manager
        self.project = project
        self.timeline = timeline

    @property
    def media_pool(self):
        return self.project.GetMediaPool() if self.project else None

    def refresh(self):
        """Re-fetch the current project and timeline from Resolve (call after switching projects)."""
        self.project = self.project_manager.GetCurrentProject()
        if self.project:
            self.timeline = self.project.GetCurrentTimeline()
        return self


def connect(host: Optional[str] = None) -> ResolveConnection:
    """
    Connect to a running DaVinci Resolve instance and return a ResolveConnection.

    Args:
        host: IP address of a remote machine running Resolve. Omit for local connection.

    Raises:
        EnvironmentError: If the scripting module cannot be found.
        ConnectionError: If Resolve is not running or scripting is disabled.
    """
    _add_resolve_to_path()

    try:
        import DaVinciResolveScript as dvr  # type: ignore
    except ModuleNotFoundError as exc:
        raise EnvironmentError(
            "DaVinci Resolve scripting module not found. "
            "Make sure DaVinci Resolve is installed, or set the RESOLVE_SCRIPT_API "
            "environment variable to its Developer/Scripting directory."
        ) from exc

    resolve = dvr.scriptapp("Resolve", host) if host else dvr.scriptapp("Resolve")

    if resolve is None:
        raise ConnectionError(
            "Could not connect to DaVinci Resolve. "
            "Ensure Resolve is open and scripting is enabled: "
            "Preferences > General > Enable local scripting API"
        )

    pm = resolve.GetProjectManager()
    if pm is None:
        raise ConnectionError("Connected to Resolve but could not get ProjectManager.")

    project = pm.GetCurrentProject()
    timeline = project.GetCurrentTimeline() if project else None

    return ResolveConnection(
        resolve=resolve,
        project_manager=pm,
        project=project,
        timeline=timeline,
    )
