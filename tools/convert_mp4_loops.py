#!/usr/bin/env python3
"""Convert MP4 expression loops to small GIFs with ffmpeg for T-RGB testing."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert MP4 loops to display-safe GIFs for T-RGB LVGL playback."
    )
    parser.add_argument("files", nargs="+", help="MP4 files to convert.")
    parser.add_argument(
        "--output-dir",
        default="examples/lv_single_image/data/gif_loops",
        help="Directory for generated GIFs.",
    )
    parser.add_argument("--size", type=int, default=480, help="Maximum GIF width/height. Defaults to 240.")
    parser.add_argument("--fps", type=int, default=8, help="Output GIF FPS. Defaults to 6.")
    parser.add_argument("--duration", type=float, default=6, help="Seconds to keep from each MP4. Defaults to 2.0.")
    parser.add_argument("--colors", type=int, default=256, help="GIF palette colors. Defaults to 64.")
    return parser.parse_args()


def convert_one(ffmpeg: str, source: Path, output_dir: Path, size: int, fps: int, duration: float, colors: int) -> Path:
    if not source.is_file():
        raise RuntimeError(f"Not a file: {source}")
    if source.suffix.lower() != ".mp4":
        raise RuntimeError(f"Expected .mp4 input: {source}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{source.stem}.gif"
    filter_graph = (
        f"fps={fps},scale={size}:-1:flags=lanczos,"
        f"split[s0][s1];[s0]palettegen=max_colors={colors}:stats_mode=diff[p];"
        f"[s1][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"
    )
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-v",
            "error",
            "-i",
            str(source),
            "-t",
            str(duration),
            "-vf",
            filter_graph,
            str(output),
        ],
        check=True,
    )
    return output


def main() -> int:
    args = parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required. Install it first, then rerun this helper.")

    output_dir = Path(args.output_dir)
    for file_text in args.files:
        output = convert_one(
            ffmpeg=ffmpeg,
            source=Path(file_text),
            output_dir=output_dir,
            size=args.size,
            fps=args.fps,
            duration=args.duration,
            colors=args.colors,
        )
        print(f"Wrote {output} ({output.stat().st_size} bytes)")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except subprocess.CalledProcessError as exc:
        print(f"Error: ffmpeg failed with exit code {exc.returncode}", file=sys.stderr)
        raise SystemExit(exc.returncode)
