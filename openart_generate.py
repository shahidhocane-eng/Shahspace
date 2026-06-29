#!/usr/bin/env python3
"""
CLI tool: generate images using the OpenArt AI API.

Usage:
  python openart_generate.py "a cinematic sunset over mountains"
  python openart_generate.py "portrait" --model flux-pro --num 4 --width 768 --height 1024 --out ./output
  python openart_generate.py "cyberpunk city" --no-download

Set OPENART_API_KEY environment variable before running.
"""

import argparse
import sys

from openart import OpenArtClient, download_images, generate_image


def main():
    parser = argparse.ArgumentParser(description="Generate images with OpenArt AI.")
    parser.add_argument("prompt", help="Text prompt to generate images from")
    parser.add_argument("--model", default=None, help="Model name (e.g. sdxl, flux-pro)")
    parser.add_argument("--num", type=int, default=1, dest="num_images", help="Number of images (default: 1)")
    parser.add_argument("--width", type=int, default=1024, help="Output width in pixels (default: 1024)")
    parser.add_argument("--height", type=int, default=1024, help="Output height in pixels (default: 1024)")
    parser.add_argument("--out", default=".", help="Output directory for downloaded images (default: .)")
    parser.add_argument("--no-download", action="store_true", help="Print URLs only, do not download")
    args = parser.parse_args()

    try:
        client = OpenArtClient()
    except EnvironmentError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Generating {args.num_images} image(s) with OpenArt AI...")
    if args.model:
        print(f"  Model     : {args.model}")
    print(f"  Prompt    : {args.prompt}")
    print(f"  Size      : {args.width}x{args.height}")

    try:
        urls = generate_image(
            client,
            args.prompt,
            model=args.model,
            num_images=args.num_images,
            width=args.width,
            height=args.height,
        )
    except RuntimeError as exc:
        print(f"[ERROR] Generation failed: {exc}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError as exc:
        print(f"[ERROR] Timed out: {exc}", file=sys.stderr)
        sys.exit(1)

    if not urls:
        print("[ERROR] No images returned.", file=sys.stderr)
        sys.exit(1)

    print(f"\nGenerated {len(urls)} image(s):")
    for url in urls:
        print(f"  {url}")

    if not args.no_download:
        print(f"\nDownloading to {args.out}/ ...")
        try:
            saved = download_images(urls, args.out)
        except Exception as exc:
            print(f"[ERROR] Download failed: {exc}", file=sys.stderr)
            sys.exit(1)
        for path in saved:
            print(f"  Saved: {path}")
        print(f"\nDone. {len(saved)} file(s) saved.")


if __name__ == "__main__":
    main()
