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
    "attention",
    "listening",
    "ack",
    "thinking",
    "deep_think",
    "recall",
    "speaking",
    "teasing",
    "annoyed",
    "proud",
    "delight",
    "concern",
    "sleepy",
    "memory",
    "uncertain",
    "boundary",
    "misheard",
    "initiate",
    "camera_curious",
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
    shape: str = "round_rect"


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
    props: tuple[tuple[str, float, float, float, float], ...] = ()
    shake_x: float = 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate low-complexity pixel-eye PNG/GIF assets for ESP32/LVGL screens. "
            "The defaults favor the current T-RGB fast GIF target: 480x480 native, short loop, few colors."
        )
    )
    parser.add_argument(
        "--output-dir",
        default="examples/lv_single_image/data/eye_assets_perf_fast",
        help="Directory for generated assets. Defaults to examples/lv_single_image/data/eye_assets_perf_fast.",
    )
    parser.add_argument(
        "--preset",
        choices=["st7789-170x320", "trgb-128", "trgb-480", "both"],
        default="trgb-480",
        help="Output size preset. Defaults to trgb-480.",
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
    parser.add_argument("--fps", type=int, default=28, help="GIF frame rate. Defaults to 28.")
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
    if args.preset == "trgb-480":
        return [("480x480", 480, 480)]
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
    if state in {"idle", "attention", "listening", "concern"} and 0.12 < t < 0.20:
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
    if state == "deep_think":
        center_y -= 7 * scale
        look = math.sin(t * math.tau * 0.65) * 3.5 * scale
    if state == "recall":
        center_y -= 3 * scale
        look = math.sin(t * math.tau * 0.75) * 1.5 * scale
    if state == "teasing":
        look = -8.0 * scale * ease_sine(clamp((t - 0.25) / 0.45, 0.0, 1.0))
    if state in {"uncertain", "misheard"}:
        look = math.sin(t * math.tau) * 2.0 * scale
    if state == "camera_curious":
        look = math.sin(t * math.tau * 0.5) * 10.0 * scale
    if state == "proud":
        look = -1.5 * scale * ease_sine(t)

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
    props: tuple[tuple[str, float, float, float, float], ...] = ()
    left_extra_h = 1.0
    left_shape = "round_rect"
    right_shape = "round_rect"

    if state == "attention":
        center_y -= 3 * scale
        spacing *= 0.9
        eye_w *= 1.04
        eye_h *= 1.18
        brightness = 1.18
        props = (("wake", center_x, center_y - 46 * scale, 12 * scale, ease_sine(t)),)
    elif state == "listening":
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
    elif state == "ack":
        center_y -= 2 * scale
        eye_w *= 1.04
        eye_h *= 0.86 + 0.06 * ease_sine(t)
        brightness = 1.14
        tilt_l = -0.02
        tilt_r = 0.02
        props = (("ok_hand", center_x + spacing / 2.0 + 22 * scale, center_y + 14 * scale, 8 * scale, ease_sine(t)),)
    elif state == "speaking":
        pulse = 0.92 + 0.10 * triangle(t * 4.0)
        eye_h *= pulse
        eye_w *= 1.02
        center_y += bounce
        brightness = 1.0 + 0.10 * triangle(t * 4.0)
        props = (
            ("speech_wave_left", center_x - spacing / 2.0 - 30 * scale, center_y + 2 * scale, 12 * scale, triangle(t * 4.0)),
            ("speech_wave_right", center_x + spacing / 2.0 + 30 * scale, center_y + 2 * scale, 12 * scale, triangle(t * 4.0)),
        )
    elif state == "teasing":
        eye_h *= 0.88
        eye_w *= 1.08
        left_shape = "wink"
        left_extra_h = 0.56
        tilt_l = 0.04
        tilt_r = -0.05
        center_y += 2 * scale
        brows = (
            (center_x - spacing / 2.0 - 17 * scale, center_y - 24 * scale, center_x - spacing / 2.0 + 14 * scale, center_y - 29 * scale),
            (center_x + spacing / 2.0 - 14 * scale, center_y - 23 * scale, center_x + spacing / 2.0 + 17 * scale, center_y - 19 * scale),
        )
        sparkle = (center_x + spacing / 2.0 + 26 * scale, center_y - 25 * scale, 4 * scale)
    elif state == "annoyed":
        shake_x = math.sin(t * math.tau * 5.0) * 2.4 * scale
        eye_h *= 0.42 + 0.05 * triangle(t * 2.0)
        eye_w *= 1.18
        tilt_l = 0.08
        tilt_r = -0.08
        center_y -= 7 * scale
        center_x += shake_x
        brows = (
            (center_x - spacing / 2.0 - 19 * scale, center_y - 21 * scale, center_x - spacing / 2.0 + 13 * scale, center_y - 31 * scale),
            (center_x + spacing / 2.0 - 13 * scale, center_y - 31 * scale, center_x + spacing / 2.0 + 19 * scale, center_y - 21 * scale),
        )
        props = (("fume_tick", center_x + spacing / 2.0 + 25 * scale, center_y - 30 * scale, 8 * scale, triangle(t * 2.0)),)
    elif state == "proud":
        center_y -= 5 * scale
        eye_w *= 1.04
        eye_h *= 1.02 + 0.08 * ease_sine(t)
        brightness = 1.10 + 0.10 * ease_sine(t)
        left_shape = "star"
        right_shape = "star"
        brows = (
            (center_x - spacing / 2.0 - 15 * scale, center_y - 24 * scale, center_x - spacing / 2.0 + 12 * scale, center_y - 19 * scale),
            (center_x + spacing / 2.0 - 12 * scale, center_y - 19 * scale, center_x + spacing / 2.0 + 15 * scale, center_y - 24 * scale),
        )
        sparkle = (center_x + spacing / 2.0 + 23 * scale, center_y - 20 * scale, (3 + 2 * ease_sine(t)) * scale)
    elif state == "delight":
        center_y -= 2 * scale
        spacing *= 0.92
        eye_w *= 1.05 + 0.08 * ease_sine(t)
        eye_h *= 1.05 + 0.08 * ease_sine(t)
        brightness = 1.20
        left_shape = "heart"
        right_shape = "heart"
        sparkle = (center_x + spacing / 2.0 + 24 * scale, center_y - 24 * scale, (4 + 3 * ease_sine(t)) * scale)
        props = (("spark_pop", center_x - spacing / 2.0 - 28 * scale, center_y - 18 * scale, 7 * scale, ease_sine(t)),)
    elif state == "concern":
        center_y += 2 * scale
        eye_w *= 1.08
        eye_h *= 0.92
        brightness = 0.86
        tilt_l = -0.10
        tilt_r = 0.10
        brows = (
            (center_x - spacing / 2.0 - 16 * scale, center_y - 24 * scale, center_x - spacing / 2.0 + 12 * scale, center_y - 29 * scale),
            (center_x + spacing / 2.0 - 12 * scale, center_y - 29 * scale, center_x + spacing / 2.0 + 16 * scale, center_y - 24 * scale),
        )
    elif state == "sleepy":
        eye_h *= 0.46
        left_shape = "sleep_arc"
        right_shape = "sleep_arc"
        brightness = 0.72
        center_y += 8 * scale
        float_up = ease_sine(t) * 10 * scale
        zzz = (center_x + spacing / 2 + 8 * scale, center_y - 24 * scale - float_up, 1.0 - t)
    elif state == "memory":
        eye_h *= 0.18
        eye_w *= 1.05
        brightness = 0.62 + 0.18 * ease_sine(t)
        antenna = (center_x, center_y - 34 * scale, 12 * scale, 8 * scale + 5 * scale * ease_sine(t))
        props = (("memory_ring", center_x, center_y + 16 * scale, 44 * scale, t),)
    elif state == "recall":
        eye_h *= 0.42
        eye_w *= 1.04
        brightness = 0.72 + 0.22 * ease_sine(t)
        antenna = (center_x, center_y - 36 * scale, 9 * scale, 8 * scale + 5 * scale * ease_sine(t))
        pupils = (
            (center_x - spacing / 2.0 + look, center_y - eye_h * 0.18, 3.0 * scale),
            (center_x + spacing / 2.0 + look, center_y - eye_h * 0.18, 3.0 * scale),
        )
        props = (("archive", center_x + 38 * scale, center_y + 35 * scale, 9 * scale, ease_sine(t)),)
    elif state == "uncertain":
        eye_w *= 0.94
        eye_h *= 0.78
        tilt_l = -0.08
        tilt_r = 0.12
        sweat = (center_x + spacing / 2 + 16 * scale, center_y - 10 * scale + triangle(t) * 5 * scale, 4 * scale)
    elif state == "misheard":
        center_y += 1 * scale
        eye_w *= 0.95
        eye_h *= 0.70
        tilt_l = 0.08
        tilt_r = -0.12
        brightness = 0.95
        receiver = (
            center_x - spacing / 2.0 - eye_w / 2.0 - 15 * scale,
            center_y,
            14 * scale,
            22 * scale,
            0.55 + 0.45 * triangle(t),
        )
        sweat = (center_x + spacing / 2 + 18 * scale, center_y - 8 * scale + triangle(t) * 4 * scale, 4 * scale)
    elif state == "thinking":
        center_y -= 2 * scale
        eye_h *= 0.96
        brightness = 0.88 + 0.10 * ease_sine(t)
        brows = (
            (center_x - spacing / 2.0 - 14 * scale, center_y - 21 * scale, center_x - spacing / 2.0 + 15 * scale, center_y - 26 * scale),
            (center_x + spacing / 2.0 - 14 * scale, center_y - 25 * scale, center_x + spacing / 2.0 + 15 * scale, center_y - 19 * scale),
        )
        antenna = (center_x, center_y - 34 * scale, 9 * scale, 8 * scale + 6 * scale * triangle(t))
        pupil_y = center_y - eye_h * 0.22 - 2 * scale * ease_sine(t)
        pupils = (
            (center_x - spacing / 2.0 + look, pupil_y, 3.5 * scale),
            (center_x + spacing / 2.0 + look, pupil_y, 3.5 * scale),
        )
        props = (("thought_bubble", center_x + spacing / 2.0 + 28 * scale, center_y - 34 * scale, 8 * scale, ease_sine(t)),)
    elif state == "deep_think":
        eye_h *= 0.62
        eye_w *= 1.08
        brightness = 0.78 + 0.08 * ease_sine(t)
        antenna = (center_x, center_y - 38 * scale, 8 * scale, 9 * scale + 8 * scale * triangle(t))
        pupils = (
            (center_x - spacing / 2.0 + look, center_y - eye_h * 0.18, 2.6 * scale),
            (center_x + spacing / 2.0 + look, center_y - eye_h * 0.18, 2.6 * scale),
        )
        props = (("deep_orbit", center_x, center_y - 2 * scale, 38 * scale, t),)
    elif state == "boundary":
        eye_h *= 0.56
        eye_w *= 1.12
        brightness = 0.82
        center_y += 1 * scale
        brows = (
            (center_x - spacing / 2.0 - 16 * scale, center_y - 23 * scale, center_x - spacing / 2.0 + 16 * scale, center_y - 23 * scale),
            (center_x + spacing / 2.0 - 16 * scale, center_y - 23 * scale, center_x + spacing / 2.0 + 16 * scale, center_y - 23 * scale),
        )
        props = (("stop_hand", center_x + spacing / 2.0 + 21 * scale, center_y + 12 * scale, 10 * scale, ease_sine(t)),)
    elif state == "initiate":
        center_x -= 5 * scale
        center_y -= 2 * scale
        spacing *= 0.9
        eye_h *= 1.04
        brightness = 1.08 + 0.08 * ease_sine(t)
        props = (("wave_hand", center_x + spacing / 2.0 + 21 * scale, center_y + 17 * scale, 9 * scale, ease_sine(t)),)
    elif state == "camera_curious":
        center_y -= 3 * scale
        eye_w *= 1.12
        eye_h *= 1.02
        brightness = 1.05
        pupils = (
            (center_x - spacing / 2.0 + look, center_y - eye_h * 0.10, 3.2 * scale),
            (center_x + spacing / 2.0 + look, center_y - eye_h * 0.10, 3.2 * scale),
        )
        props = (("scan_frame", center_x, center_y, 56 * scale, t),)

    left = Eye(center_x - spacing / 2.0 + look, center_y, eye_w, eye_h * left_extra_h, tilt_l, brightness, left_shape)
    right_extra_y = 0.0
    right_extra_h = 1.0
    if state == "uncertain":
        right_extra_y = -5 * scale
        right_extra_h = 0.72
    if state == "misheard":
        right_extra_y = -3 * scale
        right_extra_h = 0.78
    right = Eye(
        center_x + spacing / 2.0 + look,
        center_y + right_extra_y,
        eye_w,
        eye_h * right_extra_h,
        tilt_r,
        brightness,
        right_shape,
    )

    mouth = None

    return Face(
        left=left,
        right=right,
        mouth=mouth,
        smile=smile,
        pupils=pupils,
        particles=state in {"thinking", "deep_think", "recall", "memory"},
        receiver=receiver,
        brows=brows,
        sweat=sweat,
        zzz=zzz,
        antenna=antenna,
        sparkle=sparkle,
        props=props,
        shake_x=shake_x,
    )


def color_mul(rgb: tuple[int, int, int], brightness: float) -> tuple[int, int, int]:
    return tuple(int(clamp(c * brightness, 0, 255)) for c in rgb)


def rounded_rect_points(cx: float, cy: float, w: float, h: float, tilt: float) -> tuple[float, float, float, float]:
    y_shift = tilt * w
    y0 = cy - h / 2 + y_shift
    y1 = cy + h / 2 - y_shift
    if y1 < y0:
        center = (y0 + y1) / 2.0
        half = max(1.0, h * 0.12)
        y0 = center - half
        y1 = center + half
    return (cx - w / 2, y0, cx + w / 2, y1)


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


def draw_pixel_heart(
    draw: ImageDraw.ImageDraw,
    eye: Eye,
    pixel: int,
    fill: tuple[int, int, int],
) -> None:
    q = lambda v: round(v / pixel) * pixel
    scale = min(eye.w, eye.h) / 34.0
    lobe_r = max(pixel, 8 * scale)
    cx = eye.cx
    cy = eye.cy - 1.5 * scale
    left_lobe = [q(cx - 10 * scale - lobe_r), q(cy - 5 * scale - lobe_r), q(cx - 10 * scale + lobe_r), q(cy - 5 * scale + lobe_r)]
    right_lobe = [q(cx + 10 * scale - lobe_r), q(cy - 5 * scale - lobe_r), q(cx + 10 * scale + lobe_r), q(cy - 5 * scale + lobe_r)]
    body = [
        (q(cx - 24 * scale), q(cy - 2 * scale)),
        (q(cx), q(cy + 28 * scale)),
        (q(cx + 24 * scale), q(cy - 2 * scale)),
        (q(cx + 12 * scale), q(cy - 12 * scale)),
        (q(cx), q(cy - 5 * scale)),
        (q(cx - 12 * scale), q(cy - 12 * scale)),
    ]
    draw.polygon(body, fill=fill)
    draw.ellipse(left_lobe, fill=fill)
    draw.ellipse(right_lobe, fill=fill)


def draw_pixel_star(
    draw: ImageDraw.ImageDraw,
    eye: Eye,
    pixel: int,
    fill: tuple[int, int, int],
) -> None:
    q = lambda v: round(v / pixel) * pixel
    radius_outer = min(eye.w, eye.h) * 0.52
    radius_inner = radius_outer * 0.46
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = radius_outer if i % 2 == 0 else radius_inner
        points.append((q(eye.cx + math.cos(angle) * radius), q(eye.cy + math.sin(angle) * radius)))
    draw.polygon(points, fill=fill)


def draw_wink_eye(
    draw: ImageDraw.ImageDraw,
    eye: Eye,
    pixel: int,
    fill: tuple[int, int, int],
    width: int,
) -> None:
    q = lambda v: round(v / pixel) * pixel
    left = eye.cx - eye.w * 0.48
    right = eye.cx + eye.w * 0.48
    mid = eye.cx
    top = eye.cy - eye.h * 0.10
    dip = eye.cy + eye.h * 0.18
    points = []
    for i in range(9):
        progress = i / 8.0
        if progress < 0.5:
            local = progress / 0.5
            x = left + (mid - left) * local
            y = top + (dip - top) * smoothstep(local)
        else:
            local = (progress - 0.5) / 0.5
            x = mid + (right - mid) * local
            y = dip + (top - dip) * smoothstep(local)
        points.append((q(x), q(y)))
    draw.line(points, fill=fill, width=width, joint="curve")
    cap = max(pixel, width // 2)
    for x, y in (points[0], points[-1]):
        draw.rounded_rectangle([x - cap, y - cap, x + cap, y + cap], radius=cap, fill=fill)


def draw_eye(
    draw: ImageDraw.ImageDraw,
    eye: Eye,
    pixel: int,
    fill: tuple[int, int, int],
    radius: int,
    width: int | None = None,
) -> None:
    if eye.shape == "heart":
        draw_pixel_heart(draw, eye, pixel, fill)
        return
    if eye.shape == "star":
        draw_pixel_star(draw, eye, pixel, fill)
        return
    if eye.shape == "wink":
        draw_wink_eye(draw, eye, pixel, fill, width or max(pixel, int(pixel * 2.5)))
        return
    if eye.shape == "sleep_arc":
        draw_wink_eye(draw, eye, pixel, fill, width or max(pixel, int(pixel * 2.2)))
        return
    draw_pixel_rounded_rect(draw, eye, pixel, fill, radius)


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


def draw_smile_curve(
    draw: ImageDraw.ImageDraw,
    smile: tuple[float, float, float, float, float, float],
    pixel: int,
    fill: tuple[int, int, int],
    width: int,
) -> None:
    x0, y0, x1, y1, x2, y2 = smile
    q = lambda v: round(v / pixel) * pixel
    points = []
    for i in range(17):
        t = i / 16.0
        inv = 1.0 - t
        x = inv * inv * x0 + 2 * inv * t * x1 + t * t * x2
        y = inv * inv * y0 + 2 * inv * t * y1 + t * t * y2
        points.append((q(x), q(y)))
    shadow = (8, 76, 72)
    draw.line(points, fill=shadow, width=width + max(1, pixel), joint="curve")
    draw.line(points, fill=fill, width=width, joint="curve")
    cap = max(pixel, width // 2)
    for x, y in (points[0], points[-1]):
        draw.rounded_rectangle([x - cap, y - cap, x + cap, y + cap], radius=cap, fill=fill)


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


def draw_prop(draw: ImageDraw.ImageDraw, prop: tuple[str, float, float, float, float], pixel: int) -> None:
    name, cx, cy, size, phase = prop
    color = (92, 255, 238)
    dim = (24, 142, 132)
    q = lambda v: round(v / pixel) * pixel
    w = max(1, pixel)

    if name == "ok_hand":
        cy -= math.sin(phase * math.pi) * size * 0.20
        draw.ellipse([cx - size, cy - size, cx + size, cy + size], outline=color, width=max(w, pixel * 2))
        draw_pixel_line(draw, (cx + size * 0.85, cy + size * 0.2, cx + size * 1.8, cy + size * 1.0), pixel, color, width=max(w, pixel * 2))
        for i in range(3):
            x = cx - size * 0.70 + i * size * 0.42
            draw_pixel_line(draw, (x, cy + size * 0.9, x + size * 0.12, cy + size * 1.7), pixel, color, width=max(w, pixel))
        return

    if name == "stop_hand":
        cy -= math.sin(phase * math.pi) * size * 0.12
        draw.rounded_rectangle(
            [q(cx - size * 0.72), q(cy - size), q(cx + size * 0.72), q(cy + size * 0.75)],
            radius=max(pixel, int(size * 0.25)),
            outline=color,
            width=max(w, pixel * 2),
        )
        draw_pixel_line(draw, (cx - size * 0.90, cy + size * 1.0, cx + size * 0.88, cy + size * 1.0), pixel, dim, width=max(w, pixel))
        return

    if name == "wave_hand":
        swing = math.sin(phase * math.pi) * size * 0.35
        palm_x = cx + swing
        draw.rounded_rectangle(
            [q(palm_x - size * 0.55), q(cy - size * 0.30), q(palm_x + size * 0.55), q(cy + size * 0.75)],
            radius=max(pixel, int(size * 0.20)),
            fill=dim,
            outline=color,
            width=max(w, pixel),
        )
        for i in range(3):
            x = palm_x - size * 0.45 + i * size * 0.45
            draw_pixel_line(draw, (x, cy - size * 0.25, x + swing * 0.15, cy - size * 1.05), pixel, color, width=max(w, pixel))
        return

    if name == "wake":
        glow = 0.35 + 0.65 * phase
        draw.ellipse(
            [cx - size * glow, cy - size * glow, cx + size * glow, cy + size * glow],
            outline=color_mul(color, 0.55 + 0.45 * glow),
            width=max(w, pixel),
        )
        draw_pixel_line(draw, (cx, cy - size * 1.4, cx, cy - size * 0.55), pixel, color, width=max(w, pixel))
        return

    if name == "spark_pop":
        radius = size * (0.6 + 0.4 * phase)
        draw_pixel_line(draw, (cx - radius, cy, cx + radius, cy), pixel, color, width=max(1, pixel // 2))
        draw_pixel_line(draw, (cx, cy - radius, cx, cy + radius), pixel, color, width=max(1, pixel // 2))
        return

    if name == "thought_bubble":
        bob = math.sin(phase * math.pi) * size * 0.16
        for i, factor in enumerate((1.0, 0.62, 0.38)):
            ox = -i * size * 0.62
            oy = i * size * 0.58 + bob
            r = size * factor
            draw.ellipse(
                [q(cx + ox - r), q(cy + oy - r), q(cx + ox + r), q(cy + oy + r)],
                outline=color if i == 0 else dim,
                width=max(w, pixel),
            )
        return

    if name == "question":
        draw.arc([cx - size, cy - size, cx + size, cy + size], start=200, end=80, fill=color, width=max(w, pixel))
        draw.rectangle([q(cx - pixel), q(cy + size * 1.10), q(cx + pixel), q(cy + size * 1.25)], fill=color)
        return

    if name == "archive":
        draw.rounded_rectangle(
            [q(cx - size), q(cy - size * 0.65), q(cx + size), q(cy + size * 0.65)],
            radius=max(pixel, int(size * 0.15)),
            outline=color,
            width=max(w, pixel),
        )
        draw_pixel_line(draw, (cx - size * 0.65, cy - size * 0.15, cx + size * 0.65, cy - size * 0.15), pixel, dim, width=max(w, pixel))
        draw_pixel_line(draw, (cx - size * 0.35, cy + size * 0.30, cx + size * 0.35, cy + size * 0.30), pixel, color, width=max(w, pixel))
        return

    if name in {"speech_wave_left", "speech_wave_right"}:
        side = -1 if name.endswith("left") else 1
        for i in range(2):
            r = size * (0.62 + i * 0.52 + 0.14 * phase)
            box = [cx - r, cy - r * 0.88, cx + r, cy + r * 0.88]
            start = 112 if side < 0 else -68
            end = 248 if side < 0 else 68
            draw.arc(
                [q(box[0]), q(box[1]), q(box[2]), q(box[3])],
                start=start,
                end=end,
                fill=color_mul(color, 0.62 + i * 0.12 + phase * 0.16),
                width=max(1, pixel),
            )
        return

    if name == "fume_tick":
        rise = math.sin(phase * math.pi) * size * 0.25
        draw.arc([cx - size, cy - size - rise, cx + size, cy + size * 0.65 - rise], start=205, end=35, fill=color, width=max(w, pixel * 2))
        draw.arc([cx - size * 0.50, cy - size * 1.35 - rise, cx + size * 1.15, cy + size * 0.30 - rise], start=205, end=35, fill=dim, width=max(w, pixel))
        return

    if name == "soft_pulse":
        r = size * (0.55 + 0.45 * phase)
        draw.arc([cx - r, cy - r * 0.65, cx + r, cy + r * 0.65], start=205, end=335, fill=color_mul(color, 0.55 + 0.35 * phase), width=max(1, pixel))
        return

    if name == "memory_ring":
        for i in range(2):
            phase_i = (phase + i * 0.5) % 1.0
            r = size * (0.38 + phase_i * 0.30)
            alpha = 0.65 - phase_i * 0.38
            draw.arc([cx - r, cy - r * 0.50, cx + r, cy + r * 0.50], start=15, end=335, fill=color_mul(color, alpha), width=max(1, pixel))
        return

    if name == "laurel_tick":
        lift = math.sin(phase * math.pi) * size * 0.08
        for side in (-1, 1):
            base_x = cx + side * size * 0.95
            for i in range(3):
                leaf_y = cy - lift - i * size * 0.28
                leaf_x = base_x - side * i * size * 0.20
                draw.ellipse(
                    [q(leaf_x - size * 0.16), q(leaf_y - size * 0.10), q(leaf_x + size * 0.16), q(leaf_y + size * 0.10)],
                    fill=color_mul(color, 0.55 + i * 0.12),
                )
        return

    if name == "deep_orbit":
        for i in range(3):
            angle = phase * math.tau + i * math.tau / 3
            px = cx + math.cos(angle) * size * 0.62
            py = cy + math.sin(angle) * size * 0.34
            dot = max(2, pixel)
            draw.rectangle([q(px), q(py), q(px) + dot, q(py) + dot], fill=color_mul(color, 0.45 + i * 0.12))
        return

    if name == "scan_frame":
        sweep = (phase % 1.0 - 0.5) * size * 1.5
        draw.rounded_rectangle(
            [q(cx - size), q(cy - size * 0.52), q(cx + size), q(cy + size * 0.52)],
            radius=max(pixel, int(size * 0.08)),
            outline=dim,
            width=max(1, pixel),
        )
        draw_pixel_line(draw, (cx + sweep, cy - size * 0.50, cx + sweep, cy + size * 0.50), pixel, color, width=max(1, pixel))


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

    for prop in face.props:
        if prop[0] in {"scan_frame", "deep_orbit"}:
            draw_prop(draw, prop, pixel)

    for eye in (face.left, face.right):
        eye_fill = eye_color
        if eye.shape == "wink":
            draw_wink_eye(draw, eye, pixel, (8, 76, 72), width=max(pixel * 3, int(pixel * 3.2)))
            draw_wink_eye(draw, eye, pixel, color_mul(eye_fill, eye.brightness), width=max(pixel * 2, int(pixel * 2.4)))
            continue
        eye_glows = glow_colors
        for i, glow in enumerate(glow_colors):
            grow = pixel * (4 - i)
            glow_eye = Eye(eye.cx, eye.cy, eye.w + grow * 2, eye.h + grow * 2, eye.tilt, eye.brightness, eye.shape)
            draw_eye(
                draw,
                glow_eye,
                pixel,
                color_mul(eye_glows[i], eye.brightness * (0.55 + i * 0.12)),
                radius=max(pixel, int((8 + i * 2) * min(width, height) / 170)),
                width=max(pixel, pixel * (4 - i)),
            )
        draw_eye(
            draw,
            eye,
            pixel,
            color_mul(eye_fill, eye.brightness),
            radius=max(pixel, int(7 * min(width, height) / 170)),
            width=max(pixel * 2, int(pixel * 2.5)),
        )

    if face.mouth:
        draw.rounded_rectangle(face.mouth, radius=max(1, pixel // 2), fill=(80, 248, 232))

    if face.smile:
        draw_smile_curve(draw, face.smile, pixel, (80, 248, 232), width=max(pixel * 2, int(pixel * 2.2)))

    if face.pupils:
        for px, py, pr in face.pupils:
            draw.rounded_rectangle(
                [px - pr, py - pr, px + pr, py + pr],
                radius=max(1, int(pr)),
                fill=(2, 38, 38),
            )

    if face.brows:
        for brow in face.brows:
            draw_pixel_line(draw, brow, pixel, (8, 76, 72), width=max(pixel * 2, int(pixel * 2.5)))
            draw_pixel_line(draw, brow, pixel, (78, 244, 226), width=max(pixel, pixel * 2))

    if face.sparkle:
        sx, sy, sr = face.sparkle
        color = (104, 255, 238)
        draw_pixel_line(draw, (sx - sr, sy, sx + sr, sy), pixel, color, width=max(1, pixel // 2))
        draw_pixel_line(draw, (sx, sy - sr, sx, sy + sr), pixel, color, width=max(1, pixel // 2))

    for prop in face.props:
        if prop[0] not in {"scan_frame", "deep_orbit"}:
            draw_prop(draw, prop, pixel)

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
        "attention": 0.20,
        "listening": 0.50,
        "ack": 0.30,
        "thinking": 0.25,
        "deep_think": 0.35,
        "recall": 0.55,
        "speaking": 0.125,
        "teasing": 0.75,
        "annoyed": 0.125,
        "proud": 0.25,
        "delight": 0.30,
        "concern": 0.45,
        "sleepy": 0.50,
        "memory": 0.50,
        "uncertain": 0.50,
        "boundary": 0.40,
        "misheard": 0.45,
        "initiate": 0.20,
        "camera_curious": 0.35,
    }.get(state, 0.0)


def loop_t(state: str, progress: float) -> float:
    """Map loop progress to internal animation time while returning to the anchor pose."""
    anchor = anchor_t(state)
    if progress <= 0.0 or progress >= 1.0:
        return anchor

    if state == "idle":
        return progress
    if state == "attention":
        return (anchor + 0.14 * math.sin(progress * math.tau)) % 1.0
    if state == "listening":
        return (anchor + 0.04 * math.sin(progress * math.tau)) % 1.0
    if state == "ack":
        return (anchor + 0.16 * math.sin(progress * math.tau)) % 1.0
    if state == "thinking":
        return (anchor + 0.10 * math.sin(progress * math.tau)) % 1.0
    if state == "deep_think":
        return (anchor + progress * 0.8) % 1.0
    if state == "recall":
        return (anchor + 0.16 * math.sin(progress * math.tau)) % 1.0
    if state == "speaking":
        return (anchor + progress) % 1.0
    if state == "teasing":
        return (anchor - 0.50 * ease_sine(progress)) % 1.0
    if state == "annoyed":
        return (anchor + progress) % 1.0
    if state == "proud":
        return (anchor + 0.08 * math.sin(progress * math.tau)) % 1.0
    if state == "delight":
        return (anchor + 0.10 * math.sin(progress * math.tau)) % 1.0
    if state == "concern":
        return (anchor + 0.07 * math.sin(progress * math.tau)) % 1.0
    if state == "sleepy":
        return (anchor + 0.10 * math.sin(progress * math.tau)) % 1.0
    if state == "memory":
        return (anchor + 0.12 * math.sin(progress * math.tau)) % 1.0
    if state == "uncertain":
        return (anchor + 0.10 * math.sin(progress * math.tau)) % 1.0
    if state == "boundary":
        return (anchor + 0.05 * math.sin(progress * math.tau)) % 1.0
    if state == "misheard":
        return (anchor + 0.12 * math.sin(progress * math.tau)) % 1.0
    if state == "initiate":
        return (anchor + 0.18 * math.sin(progress * math.tau)) % 1.0
    if state == "camera_curious":
        return progress
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
