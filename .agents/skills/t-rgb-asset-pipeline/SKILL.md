---
name: t-rgb-asset-pipeline
description: Prepare and upload lightweight T-RGB companion visual assets. Use when new PNG/JPG stills, GIF loops, or MP4 source loops are added for examples/lv_single_image/data and Codex needs to convert, validate, upload, preview, or bind them for the LilyGo T-RGB without overloading SD-backed LVGL playback.
---

# T-RGB Asset Pipeline

Use this skill to keep T-RGB visual assets in the current low-stress format.

## Target Format

- Stills: PNG or JPG, square 128x128, uploaded to `/data`.
- GIF loops: 128x128, about 16.7 fps (`50/3`), up to 3 seconds, under 1 MB, uploaded to `/data/gif_loops/128`.
- Do not upload MP4 files to the board. Convert MP4 source loops to GIF first.
- Prefer the project helpers in `tools/`; do not rewrite conversion code when `ffmpeg`, `sips`, or the existing Python helpers can do the job.

## Workflow

1. Inspect new files under `examples/lv_single_image/data`.
2. Convert MP4 loops with:

```bash
python3 tools/convert_mp4_loops.py examples/lv_single_image/data/*.mp4
```

3. Resize/upload stills with:

```bash
python3 tools/upload_asset.py --bot-url <board-ip> examples/lv_single_image/data/<asset>.png
```

4. Upload GIF loops with:

```bash
python3 tools/upload_asset.py --bot-url <board-ip> --folder /data/gif_loops/128 examples/lv_single_image/data/gif_loops/128/<loop>.gif
```

5. Preview GIFs in clean mode before binding:

```bash
python3 tools/preview_asset.py --bot-url <board-ip> --folder /data/gif_loops/128 --clean <loop>.gif
```

6. Bind only assets that visibly work on the board:

```bash
python3 tools/bind_asset.py --bot-url <board-ip> --folder /data/gif_loops/128 LISTENING listen_loop.gif
```

## Validation

Run the bundled validator after preparing local assets:

```bash
python3 .agents/skills/t-rgb-asset-pipeline/scripts/check_t_rgb_assets.py
```

The validator checks the local repo copy for 128x128 stills, 128x128 GIF loops, sub-1 MB GIFs, and accidental MP4 or oversized test assets in the board data folder.

## If Assets Are Too Heavy

- Reduce GIF duration before reducing visible motion.
- Keep dimensions at 128x128 and let firmware zoom to the display.
- Keep GIFs below 1 MB so firmware can preload them into PSRAM instead of streaming from SD.
- If a GIF still looks slow, treat SD-backed GIF playback as the bottleneck and test a smaller/fewer-frame loop.
