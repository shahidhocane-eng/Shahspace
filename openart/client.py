"""
OpenArt AI REST API client.

Set the OPENART_API_KEY environment variable or pass api_key explicitly.
"""

import json
import os
import time
import urllib.error
import urllib.request
from typing import Optional


OPENART_BASE_URL = "https://openart.ai/api/v1"
_DEFAULT_POLL_INTERVAL = 3   # seconds
_DEFAULT_TIMEOUT = 300       # seconds


class OpenArtClient:
    """Thin wrapper around the OpenArt AI REST API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENART_API_KEY")
        if not self.api_key:
            raise EnvironmentError(
                "OpenArt API key not found. Set the OPENART_API_KEY environment "
                "variable or pass api_key= to OpenArtClient()."
            )

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        url = f"{OPENART_BASE_URL}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()
            raise RuntimeError(f"OpenArt API error {exc.code}: {detail}") from exc

    def create_image_request(self, prompt: str, **kwargs) -> str:
        """
        Submit an image generation request.

        Args:
            prompt: Text prompt.
            **kwargs: Extra API params (model, num_images, width, height, etc.).

        Returns:
            request_id string to poll with wait_for_result().
        """
        payload = {"prompt": prompt, **kwargs}
        resp = self._request("POST", "/image_requests", payload)
        return resp["id"]

    def get_image_request(self, request_id: str) -> dict:
        """Fetch the current status/result of a generation request."""
        return self._request("GET", f"/image_requests/{request_id}")

    def wait_for_result(
        self,
        request_id: str,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> dict:
        """
        Poll until the request completes or fails.

        Returns:
            The completed request dict (includes output_url list).

        Raises:
            TimeoutError: If the request does not finish within timeout seconds.
            RuntimeError: If the request failed.
        """
        deadline = time.monotonic() + timeout
        while True:
            result = self.get_image_request(request_id)
            status = result.get("status", "")
            if status == "completed":
                return result
            if status in ("failed", "error"):
                raise RuntimeError(
                    f"Image request {request_id} failed: {result.get('error', 'unknown error')}"
                )
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"Image request {request_id} did not complete within {timeout}s "
                    f"(status: {status})"
                )
            time.sleep(poll_interval)
