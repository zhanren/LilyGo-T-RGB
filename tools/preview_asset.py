#!/usr/bin/env python3
"""Preview an uploaded T-RGB SD card image on the display."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import urllib.parse

from upload_asset import normalize_bot_url, request_json, validate_folder


DISPLAYABLE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show a JPG/PNG/GIF from the T-RGB SD card without reflashing firmware."
    )
    parser.add_argument(
        "file",
        help="Asset filename or SD path, like memory.png or /data/memory.png.",
    )
    parser.add_argument(
        "--bot-url",
        required=True,
        help="Base URL for the T-RGB, like http://192.168.1.138. A bare IP also works.",
    )
    parser.add_argument(
        "--folder",
        default="/data",
        help="Folder used when file is a bare filename. Defaults to /data.",
    )
    parser.add_argument(
        "--state",
        default="PREVIEW",
        help="Badge label to show while previewing. Defaults to PREVIEW.",
    )
    parser.add_argument(
        "--text",
        default="",
        help="Bubble text to show while previewing. Defaults to the asset path.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Seconds to wait for the T-RGB preview request.",
    )
    return parser.parse_args()


def validate_displayable(file_text: str) -> None:
    suffix = Path(file_text).suffix.lower()
    if suffix not in DISPLAYABLE_EXTENSIONS:
        allowed = ", ".join(sorted(DISPLAYABLE_EXTENSIONS))
        raise RuntimeError(f"Preview supports displayable image files only: {allowed}")


def main() -> int:
    args = parse_args()
    validate_displayable(args.file)

    bot_url = normalize_bot_url(args.bot_url)
    folder = validate_folder(args.folder)
    query = urllib.parse.urlencode(
        {
            "file": args.file,
            "folder": folder,
            "state": args.state,
            "text": args.text,
        }
    )
    url = f"{bot_url}/preview?{query}"
    result = request_json(url, args.timeout)
    if not result.get("ok"):
        raise RuntimeError(f"Preview failed: {result}")

    print(f"Previewing {result.get('path')} on {bot_url}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nStopped.")
        raise SystemExit(0)
