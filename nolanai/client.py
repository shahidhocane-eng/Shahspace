"""
HTTP client for the Nolan AI Studio dashboard at https://studio.nolanai.app

Authentication: set NOLANAI_API_KEY in the environment, or pass api_key= directly.
"""

from __future__ import annotations

import os
from typing import Optional

import urllib.request
import urllib.parse
import urllib.error
import json

STUDIO_BASE_URL = "https://studio.nolanai.app"


class NolanAIError(Exception):
    """Raised when the Nolan AI Studio API returns an error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class NolanAIClient:
    """
    Client for the Nolan AI Studio API.

    Usage::

        client = NolanAIClient()          # reads NOLANAI_API_KEY from env
        client = NolanAIClient(api_key="...") # explicit key
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = STUDIO_BASE_URL,
    ):
        self.api_key = api_key or os.environ.get("NOLANAI_API_KEY")
        if not self.api_key:
            raise NolanAIError(
                "Nolan AI API key is required. "
                "Set the NOLANAI_API_KEY environment variable or pass api_key= to NolanAIClient."
            )
        self.base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, payload: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        data = json.dumps(payload).encode() if payload else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode()
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            try:
                detail = json.loads(body).get("message") or json.loads(body).get("error") or body
            except Exception:
                detail = body or str(exc)
            raise NolanAIError(f"HTTP {exc.code}: {detail}", status_code=exc.code) from exc
        except urllib.error.URLError as exc:
            raise NolanAIError(f"Network error reaching {self.base_url}: {exc.reason}") from exc

    def _get(self, path: str, **params) -> dict:
        return self._request("GET", path, params=params or None)

    def _post(self, path: str, payload: dict) -> dict:
        return self._request("POST", path, payload=payload)

    def _patch(self, path: str, payload: dict) -> dict:
        return self._request("PATCH", path, payload=payload)

    # ------------------------------------------------------------------
    # Auth / session
    # ------------------------------------------------------------------

    def ping(self) -> dict:
        """
        Verify credentials and return the authenticated user profile.

        Raises NolanAIError on auth failure or network error.
        """
        return self._get("/api/me")

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def list_projects(self) -> list[dict]:
        """Return all projects in the Nolan AI Studio account."""
        return self._get("/api/projects").get("projects", [])

    def get_project(self, project_id: str) -> dict:
        """Fetch a single project by ID."""
        return self._get(f"/api/projects/{project_id}")

    def create_project(self, name: str, description: str = "") -> dict:
        """Create a new project in Nolan AI Studio and return it."""
        return self._post("/api/projects", {"name": name, "description": description})

    # ------------------------------------------------------------------
    # Sequences (timelines)
    # ------------------------------------------------------------------

    def list_sequences(self, project_id: str) -> list[dict]:
        """Return all sequences attached to a project."""
        return self._get(f"/api/projects/{project_id}/sequences").get("sequences", [])

    def push_sequence(self, project_id: str, name: str, metadata: dict) -> dict:
        """
        Push a timeline/sequence record to a Nolan AI Studio project.

        Args:
            project_id: Nolan AI project ID.
            name:        Sequence name (matches the DaVinci Resolve timeline name).
            metadata:    Arbitrary key/value pairs (frame_rate, width, height, …).
        """
        return self._post(
            f"/api/projects/{project_id}/sequences",
            {"name": name, "metadata": metadata},
        )

    # ------------------------------------------------------------------
    # Media assets
    # ------------------------------------------------------------------

    def list_assets(self, project_id: str) -> list[dict]:
        """Return all media assets registered in a project."""
        return self._get(f"/api/projects/{project_id}/assets").get("assets", [])

    def register_asset(self, project_id: str, name: str, path: str, asset_type: str = "video") -> dict:
        """
        Register an external media asset (e.g. a clip on disk) with a Nolan AI project.

        Args:
            project_id: Nolan AI project ID.
            name:       Human-readable asset name.
            path:       Absolute path to the media file.
            asset_type: One of "video", "audio", "image".
        """
        return self._post(
            f"/api/projects/{project_id}/assets",
            {"name": name, "path": path, "type": asset_type},
        )
