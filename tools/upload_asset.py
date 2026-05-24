#!/usr/bin/env python3
"""Upload visual assets from the laptop to the T-RGB SD card."""

from __future__ import annotations

import argparse
import json
import mimetypes
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".mp4"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload JPG/PNG/GIF/MP4 files to a folder on the T-RGB SD card."
    )
    parser.add_argument("files", nargs="*", help="JPG, PNG, GIF, or MP4 files to upload.")
    parser.add_argument(
        "--bot-url",
        required=True,
        help="Base URL for the T-RGB, like http://192.168.1.123. A bare IP also works.",
    )
    parser.add_argument(
        "--folder",
        default="/data",
        help="Target SD card folder. Defaults to /data.",
    )
    parser.add_argument(
        "--name",
        help="Override the uploaded filename. Only valid when uploading one file.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List files in the target folder after the upload, or by itself.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be uploaded without contacting the T-RGB.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Seconds to wait for each T-RGB request.",
    )
    return parser.parse_args()


def normalize_bot_url(bot_url: str) -> str:
    bot_url = bot_url.strip()
    if "://" not in bot_url:
        bot_url = f"http://{bot_url}"

    parsed = urllib.parse.urlparse(bot_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise RuntimeError(f"Invalid bot URL: {bot_url}")

    return bot_url.rstrip("/")


def validate_folder(folder: str) -> str:
    folder = folder.strip() or "/data"
    if not folder.startswith("/"):
        folder = f"/{folder}"
    folder = folder.rstrip("/") or "/"
    if folder == "/" or ".." in folder or "\\" in folder:
        raise RuntimeError("Folder must be a safe SD path such as /data or /data/expressions.")
    return folder


def validate_file(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.is_file():
        raise RuntimeError(f"Not a file: {path}")
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise RuntimeError(f"Unsupported asset type for {path.name}. Use one of: {allowed}")
    return path


def encode_multipart_file(field_name: str, path: Path, upload_name: str) -> tuple[bytes, str]:
    boundary = f"----trgb-{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(upload_name)[0] or "application/octet-stream"
    chunks = [
        f"--{boundary}\r\n".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="{field_name}"; '
            f'filename="{upload_name}"\r\n'
        ).encode("utf-8"),
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
        path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode("utf-8"),
    ]
    return b"".join(chunks), boundary


def request_json(url: str, timeout: int, data: bytes | None = None, headers: dict[str, str] | None = None) -> dict:
    request = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from T-RGB:\n{body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"T-RGB request failed: {exc.reason}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"T-RGB did not return JSON:\n{body}") from exc


def upload_file(bot_url: str, folder: str, path: Path, upload_name: str, timeout: int, dry_run: bool) -> None:
    query = urllib.parse.urlencode({"folder": folder})
    url = f"{bot_url}/upload?{query}"

    if dry_run:
        print(f"DRY RUN upload {path} -> {url} as {upload_name}")
        return

    body, boundary = encode_multipart_file("file", path, upload_name)
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    result = request_json(url, timeout, data=body, headers=headers)
    if not result.get("ok"):
        raise RuntimeError(f"Upload failed for {path.name}: {result}")

    print(f"Uploaded {path.name} -> {result.get('path')} ({result.get('size')} bytes)")


def list_assets(bot_url: str, folder: str, timeout: int, dry_run: bool) -> None:
    query = urllib.parse.urlencode({"folder": folder})
    url = f"{bot_url}/assets?{query}"

    if dry_run:
        print(f"DRY RUN list {url}")
        return

    result = request_json(url, timeout)
    files = result.get("files", [])
    print(f"{result.get('folder', folder)}:")
    if not files:
        print("  (empty)")
        return
    for item in files:
        print(f"  {item.get('name')}  {item.get('size')} bytes")


def main() -> int:
    args = parse_args()
    if args.name and len(args.files) != 1:
        raise RuntimeError("--name can only be used when uploading exactly one file.")
    if not args.files and not args.list:
        raise RuntimeError("Pass at least one file to upload, or use --list.")

    bot_url = normalize_bot_url(args.bot_url)
    folder = validate_folder(args.folder)
    paths = [validate_file(file_text) for file_text in args.files]

    for path in paths:
        upload_name = args.name or path.name
        if Path(upload_name).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise RuntimeError(f"Upload name must end with JPG, PNG, GIF, or MP4: {upload_name}")
        upload_file(bot_url, folder, path, upload_name, args.timeout, args.dry_run)

    if args.list:
        list_assets(bot_url, folder, args.timeout, args.dry_run)

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
