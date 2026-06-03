#!/usr/bin/env python3
"""Generate lightweight pixel-eye PNG/GIF assets for small ESP32 displays."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterable

from PIL import Image, ImageDraw


DEFAULT_STATES = [
    "idle",
    "listening",
    "thinking",
    "speaking",
    "teasing",
    "annoyed",
    "proud",
    "sleepy",
    "memory",
    "uncertain",
]

_EYE_SCALE = 1.0  # overridden from argparse


@dataclass(frozen=True)
class Eye:
    cx: float
    cy: float
    w: float
    h: float
    tilt: float = 0.0
    brightness: float = 1.0


@dataclass(frozen=True)
class Face:
    left: Eye
    right: Eye
    mouth: tuple[float, float, float, float] | None = None
    smile: tuple[float, float, float, float, float, float] | None = None
    pupils: tuple[tuple[float, float, float], tuple[float, float, float]] | None = None
    particles: bool = False
    receiver: tuple[float, float, float, float, float] | None = None
    brows: tuple[tuple[float, float, float, float], tuple[float, float, float, float]] | None = None
    sweat: tuple[float, float, float] | None = None
    zzz: tuple[float, float, float] | None = None
    antenna: tuple[float, float, float, float] | None = None
    sparkle: tuple[float, float, float] | None = None
    shake_x: float = 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate low-complexity pixel-eye PNG/GIF assets for ESP32/LVGL screens. "
            "The defaults favor the current T-RGB fast GIF target: 5 frames, small canvas, few colors."
        )
    )
    parser.add_argument(
        "--output-dir",
        default="examples/lv_single_image/data/eye_assets_perf_fast",
        help="Directory for generated assets. Defaults to examples/lv_single_image/data/eye_assets_perf_fast.",
    )
    parser.add_argument(
        "--preset",
        choices=["st7789-170x320", "trgb-128", "both"],
        default="trgb-128",
        help="Output size preset. Defaults to trgb-128.",
    )
    parser.add_argument("--width", type=int, help="Custom canvas width. Overrides --preset.")
    parser.add_argument("--height", type=int, help="Custom canvas height. Overrides --preset.")
    parser.add_argument(
        "--eye-scale",
        type=float,
        default=0.85,
        help="Scale factor for eye size. 1.0=default, 0.85=15%% smaller. Default: 0.85",
    )
    parser.add_argument(
        "--states",
        nargs="+",
        default=DEFAULT_STATES,
        help=f"States to generate. Defaults to: {' '.join(DEFAULT_STATES)}.",
    )
    parser.add_argument("--fps", type=int, default=20, help="GIF frame rate. Defaults to 20.")
    parser.add_argument("--seconds", type=float, default=0.50, help="GIF duration. Defaults to 0.50.")
    parser.add_argument("--pixel-size", type=int, default=4, help="Pixel block size. Defaults to 4.")
    parser.add_argument("--colors", type=int, default=16, help="GIF palette colors. Defaults to 16.")
    parser.add_argument(
        "--png-only",
        action="store_true",
        help="Generate only static PNG keyframes, no GIF loops.",
    )
    parser.add_argument(
        "--include-bezel",
        action="store_true",
        help="Draw a simple dark rounded device bezel around the screen.",
    )
    parser.add_argument(
        "--no-transitions",
        dest="generate_transitions",
        action="store_false",
        help="Do not generate *_to_idle.gif transition assets.",
    )
    parser.add_argument(
        "--with-transitions",
        dest="generate_transitions",
        action="store_true",
        help="Generate *_to_idle.gif transition assets.",
    )
    parser.set_defaults(generate_transitions=False)
    return parser.parse_args()


def preset_sizes(args: argparse.Namespace) -> list[tuple[str, int, int]]:
    if args.width or args.height:
        if not args.width or not args.height:
            raise RuntimeError("Pass both --width and --height for a custom size.")
        return [(f"{args.width}x{args.height}", args.width, args.height)]

    if args.preset == "st7789-170x320":
        return [("170x320", 170, 320)]
    if args.preset == "trgb-128":
        return [("128x128", 128, 128)]
    return [("170x320", 170, 320), ("128x128", 128, 128)]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def ease_sine(t: float) -> float:
    return 0.5 - 0.5 * math.cos(t * math.tau)


def triangle(t: float) -> float:
    t %= 1.0
    return 1.0 - abs(t * 2.0 - 1.0)


def smoothstep(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def face_for_state(state: str, t: float, width: int, height: int) -> Face:
    es = _EYE_SCALE
    scale = min(width / 170.0, height / 320.0)
    if width == height:
        scale = width / 128.0

    center_x = width / 2.0
    center_y = height * (0.43 if height > width else 0.50)
    spacing = 54 * scale
    if width == height:
        spacing = 48 * scale
    base_w = 34 * scale * es
    base_h = 38 * scale * es
    if width == height:
        base_w = 30 * scale * es
        base_h = 34 * scale * es

    bounce = math.sin(t * math.tau) * 2.0 * scale
    blink = 1.0
    if state in {"idle", "listening"} and 0.12 < t < 0.20:
        blink = 0.18 + abs(t - 0.16) * 9.0
    if state == "sleepy":
        blink = 0.55 + 0.28 * math.sin(t * math.tau)
    blink = clamp(blink, 0.16, 1.0)

    look = 0.0
    if state == "idle":
        look = math.sin(t * math.tau * 0.5) * 6.0 * scale
    if state == "thinking":
        center_y -= 5 * scale
        look = math.sin(t * math.tau) * 2.0 * scale
    if state == "teasing":
        look = -8.0 * scale * ease_sine(clamp((t - 0.25) / 0.45, 0.0, 1.0))
    if state == "uncertain":
        look = math.sin(t * math.tau) * 2.0 * scale

    eye_w = base_w
    eye_h = base_h * blink
    brightness = 1.0
    tilt_l = 0.0
    tilt_r = 0.0
    receiver = None
    brows = None
    sweat = None
    zzz = None
    antenna = None
    sparkle = None
    shake_x = 0.0
    smile = None
    pupils = None
    left_extra_h = 1.0

    if state == "listening":
        center_x += 12 * scale
        spacing *= 0.82
        eye_w *= 0.88
        eye_h *= 1.08
        center_y -= 2 * scale
        brightness = 1.12
        pop = smoothstep((t - 0.08) / 0.22)
        wiggle = math.sin(t * math.tau * 2.0) * 1.2 * scale
        dish_w = (8 + 12 * pop) * scale
        dish_h = (18 + 10 * pop) * scale
        dish_gap = 7 * scale
        left_eye_x = center_x - spacing / 2.0
        receiver = (
            left_eye_x - eye_w / 2.0 - dish_gap - dish_w / 2.0 + wiggle,
            center_y,
            dish_w,
            dish_h,
            pop,
        )
    elif state == "speaking":
        pulse = 0.86 + 0.18 * triangle(t * 4.0)
        eye_h *= pulse
        center_y += bounce
        brightness = 1.0 + 0.10 * triangle(t * 4.0)
    elif state == "teasing":
        eye_h *= 0.88
        eye_w *= 1.02
        left_extra_h = 0.32
        tilt_l = 0.05
        tilt_r = -0.03
        center_y += 2 * scale
        smile_w = 22 * scale
        smile = (
            center_x - smile_w / 2,
            center_y + 38 * scale,
            center_x,
            center_y + 45 * scale,
            center_x + smile_w / 2,
            center_y + 38 * scale,
        )
        sparkle = (center_x + spacing / 2.0 + 24 * scale, center_y - 25 * scale, 4 * scale)
    elif state == "annoyed":
        shake_x = math.sin(t * math.tau * 4.0) * 2.0 * scale
        eye_h *= 0.42 + 0.08 * triangle(t * 2.0)
        eye_w *= 1.18
        tilt_l = 0.08
        tilt_r = -0.08
        center_y -= 4 * scale
        center_x += shake_x
        brows = (
            (center_x - spacing / 2.0 - 16 * scale, center_y - 20 * scale, center_x - spacing / 2.0 + 12 * scale, center_y - 28 * scale),
            (center_x + spacing / 2.0 - 12 * scale, center_y - 28 * scale, center_x + spacing / 2.0 + 16 * scale, center_y - 20 * scale),
        )
    elif state == "proud":
        center_y -= 3 * scale
        eye_w *= 1.08
        eye_h *= 0.82 + 0.08 * ease_sine(t)
        brightness = 1.08 + 0.10 * ease_sine(t)
        tilt_l = -0.04
        tilt_r = 0.04
        brows = (
            (center_x - spacing / 2.0 - 15 * scale, center_y - 24 * scale, center_x - spacing / 2.0 + 12 * scale, center_y - 19 * scale),
            (center_x + spacing / 2.0 - 12 * scale, center_y - 19 * scale, center_x + spacing / 2.0 + 15 * scale, center_y - 24 * scale),
        )
        smile_w = 24 * scale
        smile = (
            center_x - smile_w / 2,
            center_y + 38 * scale,
            center_x,
            center_y + 45 * scale,
            center_x + smile_w / 2,
            center_y + 38 * scale,
        )
        sparkle = (center_x + spacing / 2.0 + 23 * scale, center_y - 20 * scale, (3 + 2 * ease_sine(t)) * scale)
    elif state == "sleepy":
        eye_h *= 0.62
        brightness = 0.72
        center_y += 8 * scale
        float_up = ease_sine(t) * 10 * scale
        zzz = (center_x + spacing / 2 + 8 * scale, center_y - 24 * scale - float_up, 1.0 - t)
    elif state == "memory":
        eye_h *= 0.18
        eye_w *= 1.05
        brightness = 0.62 + 0.18 * ease_sine(t)
        antenna = (center_x, center_y - 34 * scale, 12 * scale, 8 * scale + 5 * scale * ease_sine(t))
    elif state == "uncertain":
        eye_w *= 0.94
        eye_h *= 0.78
        tilt_l = -0.08
        tilt_r = 0.12
        sweat = (center_x + spacing / 2 + 16 * scale, center_y - 10 * scale + triangle(t) * 5 * scale, 4 * scale)
    elif state == "thinking":
        center_y -= 2 * scale
        eye_h *= 0.96
        brightness = 0.88 + 0.10 * ease_sine(t)
        antenna = (center_x, center_y - 34 * scale, 9 * scale, 8 * scale + 6 * scale * triangle(t))
        pupil_y = center_y - eye_h * 0.22 - 2 * scale * ease_sine(t)
        pupils = (
            (center_x - spacing / 2.0 + look, pupil_y, 3.5 * scale),
            (center_x + spacing / 2.0 + look, pupil_y, 3.5 * scale),
        )

    left = Eye(center_x - spacing / 2.0 + look, center_y, eye_w, eye_h * left_extra_h, tilt_l, brightness)
    right_extra_y = 0.0
    right_extra_h = 1.0
    if state == "uncertain":
        right_extra_y = -5 * scale
        right_extra_h = 0.72
    right = Eye(
        center_x + spacing / 2.0 + look,
        center_y + right_extra_y,
        eye_w,
        eye_h * right_extra_h,
        tilt_r,
        brightness,
    )

    mouth = None
    if state == "speaking":
        open_amount = triangle(t * 4.0)
        mouth_w = 20 * scale
        mouth_h = (3 + 10 * open_amount) * scale
        mouth = (center_x - mouth_w / 2, center_y + 40 * scale, center_x + mouth_w / 2, center_y + 40 * scale + mouth_h)

    return Face(
        left=left,
        right=right,
        mouth=mouth,
        smile=smile,
        pupils=pupils,
        particles=state in {"thinking", "memory"},
        receiver=receiver,
        brows=brows,
        sweat=sweat,
        zzz=zzz,
        antenna=antenna,
        sparkle=sparkle,
        shake_x=shake_x,
    )


def color_mul(rgb: tuple[int, int, int], brightness: float) -> tuple[int, int, int]:
    return tuple(int(clamp(c * brightness, 0, 255)) for c in rgb)


def rounded_rect_points(cx: float, cy: float, w: float, h: float, tilt: float) -> tuple[float, float, float, float]:
    y_shift = tilt * w
    return (cx - w / 2, cy - h / 2 + y_shift, cx + w / 2, cy + h / 2 - y_shift)


def draw_pixel_rounded_rect(
    draw: ImageDraw.ImageDraw,
    eye: Eye,
    pixel: int,
    fill: tuple[int, int, int],
    radius: int,
) -> None:
    x0, y0, x1, y1 = rounded_rect_points(eye.cx, eye.cy, eye.w, eye.h, eye.tilt)
    x0 = round(x0 / pixel) * pixel
    y0 = round(y0 / pixel) * pixel
    x1 = round(x1 / pixel) * pixel
    y1 = round(y1 / pixel) * pixel
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)


def draw_pixel_line(
    draw: ImageDraw.ImageDraw,
    points: tuple[float, float, float, float],
    pixel: int,
    fill: tuple[int, int, int],
    width: int | None = None,
) -> None:
    x0, y0, x1, y1 = points
    q = lambda v: round(v / pixel) * pixel
    draw.line([q(x0), q(y0), q(x1), q(y1)], fill=fill, width=width or max(1, pixel))


def draw_listening_receiver(draw: ImageDraw.ImageDraw, receiver: tuple[float, float, float, float, float], pixel: int) -> None:
    cx, cy, w, h, pop = receiver
    outer = (18, 142, 132)
    inner = (103, 255, 238)
    x0 = cx - w / 2
    y0 = cy - h / 2
    x1 = cx + w / 2
    y1 = cy + h / 2
    # Large side receiver: a C-shaped dish plus a bright inner pickup.
    draw.rounded_rectangle([x0, y0, x1, y1], radius=max(pixel, int(h / 2)), fill=outer)
    bite = w * 0.35
    draw.rectangle([x0 + bite, y0 + pixel, x1 + pixel, y1 - pixel], fill=(2, 4, 7))
    inner_x0 = x0 + pixel
    inner_x1 = max(inner_x0 + pixel, x0 + w * 0.42)
    draw.rounded_rectangle(
        [inner_x0, y0 + h * 0.24, inner_x1, y1 - h * 0.24],
        radius=max(pixel, int(h * 0.18)),
        fill=inner,
    )
    wave_color = (62, 222, 210)
    wave_gap = max(pixel, int(w * 0.18))
    for i in range(2):
        pad = wave_gap * (i + 1) * (0.75 + 0.25 * pop)
        draw.arc(
            [x0 - pad, y0 - pad, x1 + pad * 0.35, y1 + pad],
            start=125,
            end=235,
            fill=wave_color,
            width=max(1, pixel // 2),
        )


def draw_face(width: int, height: int, state: str, t: float, pixel: int, include_bezel: bool) -> Image.Image:
    img = Image.new("RGB", (width, height), (2, 4, 7))
    draw = ImageDraw.Draw(img)

    if include_bezel:
        margin = max(4, pixel * 2)
        draw.rounded_rectangle(
            [margin, margin, width - margin - 1, height - margin - 1],
            radius=max(12, int(min(width, height) * 0.12)),
            fill=(18, 20, 25),
            outline=(56, 60, 66),
            width=max(2, pixel),
        )
        screen_margin = margin + max(4, pixel)
        draw.rounded_rectangle(
            [screen_margin, screen_margin, width - screen_margin - 1, height - screen_margin - 1],
            radius=max(10, int(min(width, height) * 0.09)),
            fill=(2, 4, 7),
        )

    face = face_for_state(state, t, width, height)
    eye_color = (107, 255, 238)
    glow_colors = [
        (12, 96, 92),
        (16, 130, 122),
        (40, 190, 178),
    ]

    if face.antenna:
        ax, ay, aw, ah = face.antenna
        stem_color = (19, 118, 110)
        bulb_color = (95, 255, 238)
        draw_pixel_line(draw, (ax, ay + ah, ax, ay), pixel, stem_color, width=max(1, pixel))
        draw.rounded_rectangle(
            [ax - aw / 2, ay - aw / 2, ax + aw / 2, ay + aw / 2],
            radius=max(1, int(aw / 2)),
            fill=bulb_color,
        )

    if face.receiver:
        draw_listening_receiver(draw, face.receiver, pixel)

    for eye in (face.left, face.right):
        for i, glow in enumerate(glow_colors):
            grow = pixel * (4 - i)
            glow_eye = Eye(eye.cx, eye.cy, eye.w + grow * 2, eye.h + grow * 2, eye.tilt, eye.brightness)
            draw_pixel_rounded_rect(
                draw,
                glow_eye,
                pixel,
                color_mul(glow, eye.brightness * (0.55 + i * 0.12)),
                radius=max(pixel, int((8 + i * 2) * min(width, height) / 170)),
            )
        draw_pixel_rounded_rect(
            draw,
            eye,
            pixel,
            color_mul(eye_color, eye.brightness),
            radius=max(pixel, int(7 * min(width, height) / 170)),
        )

    if face.mouth:
        draw.rounded_rectangle(face.mouth, radius=max(1, pixel // 2), fill=(80, 248, 232))

    if face.smile:
        x0, y0, x1, y1, x2, y2 = face.smile
        q = lambda v: round(v / pixel) * pixel
        draw.line([q(x0), q(y0), q(x1), q(y1), q(x2), q(y2)], fill=(80, 248, 232), width=max(1, pixel))

    if face.pupils:
        for px, py, pr in face.pupils:
            draw.rounded_rectangle(
                [px - pr, py - pr, px + pr, py + pr],
                radius=max(1, int(pr)),
                fill=(2, 38, 38),
            )

    if face.brows:
        for brow in face.brows:
            draw_pixel_line(draw, brow, pixel, (78, 244, 226), width=max(1, pixel))

    if face.sparkle:
        sx, sy, sr = face.sparkle
        color = (104, 255, 238)
        draw_pixel_line(draw, (sx - sr, sy, sx + sr, sy), pixel, color, width=max(1, pixel // 2))
        draw_pixel_line(draw, (sx, sy - sr, sx, sy + sr), pixel, color, width=max(1, pixel // 2))

    if face.sweat:
        sx, sy, sr = face.sweat
        draw.polygon(
            [
                (sx, sy - sr),
                (sx + sr, sy),
                (sx, sy + sr * 1.4),
                (sx - sr, sy),
            ],
            fill=(92, 232, 255),
        )

    if face.zzz:
        zx, zy, fade = face.zzz
        color = color_mul((98, 255, 238), 0.35 + 0.45 * fade)
        step = max(2, pixel)
        draw_pixel_line(draw, (zx, zy, zx + 10 * step / 3, zy), pixel, color, width=max(1, pixel))
        draw_pixel_line(draw, (zx + 10 * step / 3, zy, zx, zy + 8 * step / 3), pixel, color, width=max(1, pixel))
        draw_pixel_line(draw, (zx, zy + 8 * step / 3, zx + 10 * step / 3, zy + 8 * step / 3), pixel, color, width=max(1, pixel))

    if face.particles:
        for i in range(5):
            phase = (t + i * 0.19) % 1.0
            angle = phase * math.tau + i
            radius = (28 + i * 7) * min(width, height) / 170
            px = width / 2 + math.cos(angle) * radius
            py = height * (0.43 if height > width else 0.42) + math.sin(angle) * radius * 0.55
            size = max(2, pixel // 2 + (i % 2))
            brightness = 0.25 + 0.45 * ease_sine(phase)
            draw.rectangle(
                [
                    round(px / pixel) * pixel,
                    round(py / pixel) * pixel,
                    round(px / pixel) * pixel + size,
                    round(py / pixel) * pixel + size,
                ],
                fill=color_mul((75, 255, 236), brightness),
            )

    return img


def quantize_for_gif(frame: Image.Image, colors: int) -> Image.Image:
    palette_source = frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors)
    return frame.quantize(palette=palette_source)


def save_png(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def make_contact_sheet(
    target: Path,
    states: list[str],
    width: int,
    height: int,
    pixel_size: int,
    include_bezel: bool,
) -> Path:
    thumb_max = 96
    cols = 3
    rows = math.ceil(len(states) / cols)
    pad = 8
    label_h = 14
    cell_w = thumb_max + pad * 2
    cell_h = thumb_max + label_h + pad * 2
    sheet = Image.new("RGB", (cell_w * cols, cell_h * rows), (16, 18, 22))
    draw = ImageDraw.Draw(sheet)

    for idx, state in enumerate(states):
        frame = draw_face(width, height, state, anchor_t(state), pixel_size, include_bezel)
        frame.thumbnail((thumb_max, thumb_max), Image.Resampling.NEAREST)
        col = idx % cols
        row = idx // cols
        x = col * cell_w + (cell_w - frame.width) // 2
        y = row * cell_h + pad
        sheet.paste(frame, (x, y))
        draw.text((col * cell_w + pad, row * cell_h + pad + thumb_max), state, fill=(170, 240, 232))

    output = target / "contact_sheet.png"
    save_png(output, sheet)
    return output


def save_gif(path: Path, frames: Iterable[Image.Image], fps: int, colors: int) -> None:
    marked_frames = []
    marker_colors = [(0, 0, 0), (7, 7, 10), (0, 6, 10), (7, 0, 10)]
    for index, frame in enumerate(frames):
        marked = frame.copy()
        # Prevent duplicate-looking frames from being merged into long GIF pauses.
        marker = marker_colors[index % len(marker_colors)]
        marked.putpixel((0, 0), marker)
        marked.putpixel((1, 0), marker)
        marked.putpixel((0, 1), marker)
        marked.putpixel((1, 1), marker)
        marked_frames.append(marked)

    frame_list = [quantize_for_gif(frame, colors) for frame in marked_frames]
    if not frame_list:
        raise RuntimeError("No frames generated.")
    if len(frame_list) > 1 and len({frame.tobytes() for frame in frame_list}) < 2:
        raise RuntimeError(f"Generated GIF frames are static for {path.name}. Add state motion.")
    duration_ms = max(20, int(1000 / fps))
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_list[0].save(
        path,
        save_all=True,
        append_images=frame_list[1:],
        duration=duration_ms,
        loop=0,
        optimize=False,
        disposal=2,
    )


def save_transition_to_idle(
    target: Path,
    state: str,
    width: int,
    height: int,
    fps: int,
    pixel_size: int,
    colors: int,
    include_bezel: bool,
) -> Path:
    frame_count = max(6, int(fps * 0.75))
    state_anchor = draw_face(width, height, state, anchor_t(state), pixel_size, include_bezel)
    idle_anchor = draw_face(width, height, "idle", anchor_t("idle"), pixel_size, include_bezel)
    frames = []
    for i in range(frame_count):
        progress = i / max(1, frame_count - 1)
        eased = smoothstep(progress)
        frame = Image.blend(state_anchor, idle_anchor, eased)
        frames.append(frame)
    output = target / f"{state}_to_idle.gif"
    save_gif(output, frames, fps, colors)
    return output


def anchor_t(state: str) -> float:
    return {
        "idle": 0.0,
        "listening": 0.50,
        "thinking": 0.25,
        "speaking": 0.125,
        "teasing": 0.75,
        "annoyed": 0.125,
        "proud": 0.25,
        "sleepy": 0.50,
        "memory": 0.50,
        "uncertain": 0.50,
    }.get(state, 0.0)


def loop_t(state: str, progress: float) -> float:
    """Map loop progress to internal animation time while returning to the anchor pose."""
    anchor = anchor_t(state)
    if progress <= 0.0 or progress >= 1.0:
        return anchor

    if state == "idle":
        return progress
    if state == "listening":
        return (anchor + 0.04 * math.sin(progress * math.tau)) % 1.0
    if state == "thinking":
        return (anchor + 0.10 * math.sin(progress * math.tau)) % 1.0
    if state == "speaking":
        return (anchor + progress) % 1.0
    if state == "teasing":
        return (anchor - 0.50 * ease_sine(progress)) % 1.0
    if state == "annoyed":
        return (anchor + progress) % 1.0
    if state == "proud":
        return (anchor + 0.08 * math.sin(progress * math.tau)) % 1.0
    if state == "sleepy":
        return (anchor + 0.10 * math.sin(progress * math.tau)) % 1.0
    if state == "memory":
        return (anchor + 0.12 * math.sin(progress * math.tau)) % 1.0
    if state == "uncertain":
        return (anchor + 0.10 * math.sin(progress * math.tau)) % 1.0
    return anchor


def generate_set(
    output_dir: Path,
    label: str,
    width: int,
    height: int,
    states: list[str],
    fps: int,
    seconds: float,
    pixel_size: int,
    colors: int,
    png_only: bool,
    include_bezel: bool,
    generate_transitions: bool,
) -> None:
    frames_count = max(1, int(fps * seconds))
    target = output_dir / label
    for state in states:
        if state not in DEFAULT_STATES:
            raise RuntimeError(f"Unknown state: {state}. Known states: {', '.join(DEFAULT_STATES)}")
        keyframe = draw_face(width, height, state, anchor_t(state), pixel_size, include_bezel)
        png_path = target / f"{state}.png"
        save_png(png_path, keyframe)
        print(f"Wrote {png_path} ({png_path.stat().st_size} bytes)")

        if png_only:
            continue

        denominator = max(1, frames_count - 1)
        frames = [
            draw_face(width, height, state, loop_t(state, i / denominator), pixel_size, include_bezel)
            for i in range(frames_count)
        ]
        gif_path = target / f"{state}_loop.gif"
        save_gif(gif_path, frames, fps, colors)
        print(f"Wrote {gif_path} ({gif_path.stat().st_size} bytes)")

        if generate_transitions and state != "idle":
            transition_path = save_transition_to_idle(
                target=target,
                state=state,
                width=width,
                height=height,
                fps=fps,
                pixel_size=pixel_size,
                colors=colors,
                include_bezel=include_bezel,
            )
            print(f"Wrote {transition_path} ({transition_path.stat().st_size} bytes)")

    contact_sheet = make_contact_sheet(target, states, width, height, pixel_size, include_bezel)
    print(f"Wrote {contact_sheet} ({contact_sheet.stat().st_size} bytes)")


def main() -> int:
    global _EYE_SCALE
    args = parse_args()
    _EYE_SCALE = args.eye_scale
    output_dir = Path(args.output_dir)
    for label, width, height in preset_sizes(args):
        pixel_size = max(1, args.pixel_size)
        if label in {"128", "128x128"} and args.pixel_size == 4:
            pixel_size = 3
        generate_set(
            output_dir=output_dir,
            label=label,
            width=width,
            height=height,
            states=args.states,
            fps=args.fps,
            seconds=args.seconds,
            pixel_size=pixel_size,
            colors=args.colors,
            png_only=args.png_only,
            include_bezel=args.include_bezel,
            generate_transitions=args.generate_transitions,
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
