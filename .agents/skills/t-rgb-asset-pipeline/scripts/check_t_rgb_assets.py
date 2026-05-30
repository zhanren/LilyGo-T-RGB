#!/usr/bin/env python3
"""Validate local T-RGB visual assets are in the lightweight board format."""

from __future__ import annotations

import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = ROOT / "examples" / "lv_single_image" / "data"
GIF_DIR = DATA_DIR / "gif_loops"
GIF_128_DIR = GIF_DIR / "128"
MAX_GIF_BYTES = 1024 * 1024
TARGET_SIZE = (128, 128)


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as file:
        header = file.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    return struct.unpack(">II", header[16:24])


def gif_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as file:
        header = file.read(10)
    if header[:6] not in (b"GIF87a", b"GIF89a"):
        raise ValueError("not a GIF")
    return struct.unpack("<HH", header[6:10])


def jpeg_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("not a JPEG")

    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in (0xD8, 0xD9):
            continue
        if i + 2 > len(data):
            break
        length = struct.unpack(">H", data[i:i + 2])[0]
        if marker in range(0xC0, 0xC4):
            height, width = struct.unpack(">HH", data[i + 3:i + 7])
            return width, height
        i += length
    raise ValueError("JPEG dimensions not found")


def image_size(path: Path) -> tuple[int, int]:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return png_size(path)
    if suffix in (".jpg", ".jpeg"):
        return jpeg_size(path)
    if suffix == ".gif":
        return gif_size(path)
    raise ValueError(f"unsupported extension {suffix}")


def main() -> int:
    errors: list[str] = []

    for path in sorted(DATA_DIR.glob("*")):
        if path.is_dir():
            continue
        suffix = path.suffix.lower()
        if suffix == ".mp4":
            errors.append(f"remove MP4 source from board data folder: {path}")
        elif suffix in (".png", ".jpg", ".jpeg"):
            size = image_size(path)
            if size != TARGET_SIZE:
                errors.append(f"still must be 128x128: {path} is {size[0]}x{size[1]}")
        elif suffix == ".gif":
            errors.append(f"move GIF loops into gif_loops/128: {path}")
        elif path.name != ".DS_Store":
            errors.append(f"unexpected file in data folder: {path}")

    if GIF_DIR.exists():
        for child in sorted(GIF_DIR.iterdir()):
            if child.is_dir() and child.name != "128":
                errors.append(f"remove non-target GIF folder: {child}")
            elif child.is_file():
                errors.append(f"move GIF loop into gif_loops/128: {child}")

    if not GIF_128_DIR.exists():
        errors.append(f"missing GIF target folder: {GIF_128_DIR}")
    else:
        for gif in sorted(GIF_128_DIR.glob("*.gif")):
            size = image_size(gif)
            if size != TARGET_SIZE:
                errors.append(f"GIF must be 128x128: {gif} is {size[0]}x{size[1]}")
            byte_count = gif.stat().st_size
            if byte_count >= MAX_GIF_BYTES:
                errors.append(f"GIF must be under 1 MB: {gif} is {byte_count} bytes")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("T-RGB assets look ready: 128x128 stills, 128x128 GIF loops, no oversized board data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
