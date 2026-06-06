---
name: t-rgb-asset-pipeline
description: Prepare and upload lightweight T-RGB companion visual assets. Use when new PNG/JPG stills or GIF loops are added and need to be converted, validated, uploaded, previewed, or bound for the LilyGo T-RGB.
---

# T-RGB Asset Pipeline

## Target Format

- **Expression GIF loops**: 480×480 native, ~14 frames, ~28 fps (~36 ms/frame), 16–256 colors,
  usually under 80 KB. Upload to `/data/gif_loops/480/`.
- **Stills (if used)**: PNG or JPG, square 480×480, uploaded to `/data`.
- **Source folder**: `examples/lv_single_image/data/eye_assets_perf_fast/480x480/`.
- **Do NOT** use zoomed 128×128 GIFs — software zoom adds ~10 ms/frame which visibly slows
  animation. 480×480 native with `gif_fast` pre-decode is the only fast path.
- **Expression vocabulary**: generate the full companion set:
  `idle`, `attention`, `listening`, `ack`, `thinking`, `deep_think`, `recall`, `speaking`,
  `teasing`, `annoyed`, `proud`, `delight`, `concern`, `sleepy`, `memory`, `uncertain`,
  `boundary`, `misheard`, `initiate`, `camera_curious`.
- **Body/prop cues** are allowed when they improve readability on the round display, such as
  the listening ear, an OK hand for `ack`, a stop hand for `boundary`, or a small wave for
  `initiate`. Do not add props just to decorate; the face should still carry the emotion.
- **One-theme rule**: expression may change shape, scale, pose, timing, and brightness, but
  should stay in the cyan/teal companion palette unless the whole set is rethemed.
- **Emoji/Giphy research rule**: use popular animated emoji as references for silhouette and
  motion language only. Re-author the cue in the local T-RGB style instead of copying source art.

## Firmware Architecture

- `src/gif_fast.h/cpp` — pre-decodes all GIF frames into PSRAM at load time (~150 ms for
  10 frames at 480×480). Playback is zero-overhead pointer swaps at the GIF's native frame
  rate.
- `src/LV_Helper.cpp` — single half-height LVGL draw buffer (saves ~700 KB PSRAM for
  pre-decoded frames).
- `examples/lv_single_image/main.cpp` — clean display (chrome hidden), ambient eye-state
  cycling with GIF loops.

## Workflow

### 1. Generate eye GIFs

```bash
python3 tools/generate_eye_assets.py \
  --width 480 --height 480 \
  --eye-scale 0.85 \
  --fps 28 --seconds 0.50
```

This writes the 20-state `*_loop.gif` + still PNGs + `contact_sheet.png` into
`examples/lv_single_image/data/eye_assets_perf_fast/480x480/`.
Review `contact_sheet.png` before uploading. If a cue is clipped, too tiny, or too similar to
another state, tune the generator first.

### 2. Upload to board

```bash
python3 tools/upload_asset.py \
  --bot-url <board-ip> \
  --folder /data/gif_loops/480 \
  examples/lv_single_image/data/eye_assets_perf_fast/480x480/*_loop.gif \
  --no-resize --list
```

### 3. Preview in clean mode

```bash
python3 tools/preview_asset.py \
  --bot-url <board-ip> \
  --folder /data/gif_loops/480 \
  --clean idle_loop.gif
```

### 4. Bind expression states

```bash
curl "http://<board-ip>/bind?state=IDLE&path=/data/gif_loops/480/idle_loop.gif"
curl "http://<board-ip>/bind?state=LISTENING&path=/data/gif_loops/480/listening_loop.gif"
# ... all generated states
```

Or use `tools/bind_asset.py`:
```bash
python3 tools/bind_asset.py --bot-url <board-ip> --folder /data/gif_loops/480 IDLE idle_loop.gif
```

## Validation

```bash
python3 .agents/skills/t-rgb-asset-pipeline/scripts/check_t_rgb_assets.py
```

The validator checks for 480×480 GIF loops, sub-1 MB files, and no accidental MP4 or
oversized test assets in the board data folder.

## Performance Rules

- **Always 480×480 native** — the firmware does not zoom GIF frames. Zoom costs ~10 ms/frame.
- **Use `gif_fast` not `lv_gif`** — pre-decoding eliminates per-frame LZW cost.
- **28 fps generator setting** — compensates for one-time decode overhead (~150 ms). The
  playback loop runs at the GIF's exact frame delays.
- **Keep GIFs under 1 MB** — larger files exceed the PSRAM pre-load buffer.
- **Eyes 15% smaller** (`--eye-scale 0.85`) — improves readability on the round display
  without losing state cues.
- **Prefer staged motion** — anticipation, hold, and return-to-anchor read better than constant
  jitter. Use short loops for common states and longer holds in firmware for thinking/recall.
- **Avoid debug-line faces** — mouths and brows should use thick curved/capped strokes or filled
  shapes, not single thin lines.
- **Do not spam mouths** — most states should read through eye shape, gaze, pose, and motion.
  Use a mouth only when it is the primary state cue and visually integrated.
- **No floating punctuation signs** — avoid question marks/exclamation marks as shortcuts.
  Prefer asymmetry, sweat, receiver motion, thought-bubble geometry, or other integrated cues.
- **Speaking cue** — use side speech waves, eye pulse, or glow rhythm. Avoid equalizer bars
  under the face and avoid a pasted-on mouth.

## If an Animation Feels Slow

- Increase `--fps` in the generator (try 32–35). Shorter delays compensate for any
  remaining overhead.
- Reduce `--seconds` for a tighter loop (0.35–0.40 gives 10–13 frames).
- Verify the GIF is native 480×480 (not a zoomed smaller version).
- Compare against the reference: Pikachu.gif at 480×480 native plays at the same speed
  on laptop and T-RGB.
