#!/usr/bin/env python3
"""Bind T-RGB expression states to uploaded SD card image assets."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import urllib.parse

from upload_asset import normalize_bot_url, request_json, validate_folder


DISPLAYABLE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Persistently bind an expression state to a JPG/PNG/GIF on the T-RGB SD card."
    )
    parser.add_argument(
        "state",
        nargs="?",
        help="Expression state, such as PROUD, MEMORY, TEASING, or UNCERTAIN.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Asset filename or SD path, like pround.png or /data/pround.png.",
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
        "--list",
        action="store_true",
        help="List current state bindings.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the named state to its firmware default asset.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Seconds to wait for the T-RGB request.",
    )
    return parser.parse_args()


def validate_displayable(file_text: str) -> None:
    suffix = Path(file_text).suffix.lower()
    if suffix not in DISPLAYABLE_EXTENSIONS:
        allowed = ", ".join(sorted(DISPLAYABLE_EXTENSIONS))
        raise RuntimeError(f"State bindings support displayable image files only: {allowed}")


def list_bindings(bot_url: str, timeout: int) -> None:
    result = request_json(f"{bot_url}/bindings", timeout)
    for item in result.get("bindings", []):
        marker = "" if item.get("asset") == item.get("default_asset") else " *"
        print(f"{item.get('state'):12} {item.get('asset')}{marker}")


def bind_asset(bot_url: str, folder: str, state: str, file_text: str, reset: bool, timeout: int) -> None:
    query = {
        "state": state,
        "folder": folder,
    }
    if reset:
        query["reset"] = "1"
    else:
        validate_displayable(file_text)
        query["file"] = file_text

    url = f"{bot_url}/bind?{urllib.parse.urlencode(query)}"
    result = request_json(url, timeout)
    if not result.get("ok"):
        raise RuntimeError(f"Bind failed: {result}")
    print(f"{result.get('state')} -> {result.get('asset')}")


def main() -> int:
    args = parse_args()
    bot_url = normalize_bot_url(args.bot_url)

    if args.list:
        list_bindings(bot_url, args.timeout)
        return 0

    if not args.state:
        raise RuntimeError("Pass a state, or use --list.")
    if not args.reset and not args.file:
        raise RuntimeError("Pass an asset file, or use --reset with a state.")

    folder = validate_folder(args.folder)
    bind_asset(bot_url, folder, args.state, args.file or "", args.reset, args.timeout)
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
