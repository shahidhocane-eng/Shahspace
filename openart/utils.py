"""
High-level helpers built on top of OpenArtClient.
"""

from __future__ import annotations

import os
import urllib.request
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .client import OpenArtClient


def generate_image(
    client: "OpenArtClient",
    prompt: str,
    *,
    model: Optional[str] = None,
    num_images: int = 1,
    width: int = 1024,
    height: int = 1024,
    **kwargs,
) -> list[str]:
    """
    Generate images from a text prompt and return a list of image URLs.

    Args:
        client: Authenticated OpenArtClient.
        prompt: Text prompt.
        model: Model name (e.g. "sdxl", "flux-pro"). Defaults to OpenArt's default.
        num_images: Number of images to generate (1-4).
        width: Output width in pixels.
        height: Output height in pixels.
        **kwargs: Extra API parameters forwarded to the request.

    Returns:
        List of image URLs from the completed request.
    """
    params: dict = {"num_images": num_images, "width": width, "height": height}
    if model:
        params["model"] = model
    params.update(kwargs)

    request_id = client.create_image_request(prompt, **params)
    result = client.wait_for_result(request_id)
    return result.get("output_url", [])


def download_images(urls: list[str], output_dir: str = ".") -> list[str]:
    """
    Download images from a list of URLs to a local directory.

    Args:
        urls: List of image URLs returned by generate_image().
        output_dir: Directory to save files (created if missing).

    Returns:
        List of saved file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    saved = []
    for i, url in enumerate(urls):
        ext = url.split("?")[0].rsplit(".", 1)[-1] if "." in url.split("?")[0] else "png"
        filename = os.path.join(output_dir, f"openart_{i + 1:03d}.{ext}")
        urllib.request.urlretrieve(url, filename)
        saved.append(filename)
    return saved
