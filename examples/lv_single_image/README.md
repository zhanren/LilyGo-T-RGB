# LV Single Image Bot Milestones

This is the active LilyGo T-RGB bot-face sketch. It displays face-state images from the SD card, connects to Wi-Fi, and accepts text from your laptop over HTTP.

## Current Milestones

- Week 2: show a custom image from SD card.
- Week 3: cycle named face states.
- Week 4: show a bottom text bubble.
- Week 5: connect to Wi-Fi and show the board IP.
- Week 6: receive laptop text at `/say`.
- Week 7: laptop script asks DeepSeek, then sends the answer to `/say`.
- Week 8: DeepSeek chooses both face state and text.
- Week 9: laptop speaks replies with macOS TTS.
- Week 10/11: use laptop/Bluetooth audio while the T-RGB handles face and text display.
- Week 12: prove the T-RGB can write local memory files to the SD card.
- Week 13: start the companion personality contract and append interaction moments to `/memory/moments.jsonl`.
- Week 14: add the first presence-first personality loop with richer expression states, ambient micro-motion, and a `/personality` contract endpoint.
- Week 15: upload display-ready JPG, PNG, and GIF visual assets to a chosen SD card folder over Wi-Fi.
- Week 16: preview any uploaded JPG, PNG, or GIF on the display without reflashing firmware.
- Week 17: resize JPG/PNG stills during upload so large generated assets stay display-safe.
- Week 18: bind expression states to uploaded still assets at runtime and persist the mapping on the SD card.
- Week 19: render uploaded GIF loops for animated expression states.
- Week 20: convert MP4 source loops to lightweight 128px GIFs with `ffmpeg` for smoother T-RGB testing.

## SD Card Files

Copy the contents of `examples/lv_single_image/data` to the SD card so the board has:

```text
/data/main.png
/data/innocent.png
/data/confused.png
/data/surprised.png
/data/wink.png
/data/angry.png
/data/pround.png
/data/sad.png
/data/memory.png
/data/uncertain.png
/data/gif_loops/128/listen_loop.gif
/data/gif_loops/128/think_loop.gif
/data/gif_loops/128/speak_loop.gif
/data/gif_loops/128/teasing_loop.gif
/data/gif_loops/128/memory_organizing_loop.gif
```

The T-RGB cannot read a macOS path like `/Users/...` while it is running. The images must be on the board's SD card.

## Wi-Fi Setup

Create `examples/lv_single_image/wifi_config.h` from `wifi_config.example.h`:

```cpp
#pragma once

#define WIFI_SSID "Your WiFi Name"
#define WIFI_PASSWORD "Your WiFi Password"
```

`wifi_config.h` is ignored by git so your password stays local.

## Run The Firmware

1. Insert the SD card into the T-RGB.
2. Build and upload the `examples/lv_single_image` sketch.
3. Open Serial Monitor at `115200`.
4. Note the IP shown on screen, like `192.168.1.123`.

Try the HTTP endpoint from your laptop browser:

```text
http://192.168.1.123/say?state=HAPPY&text=Hello%20from%20my%20laptop
```

Supported states are `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `TEASING`, `ANNOYED`, `PROUD`, `SLEEPY`, `MEMORY`, `UNCERTAIN`, plus the older image-demo states `HAPPY`, `DISTRACTED`, `MAD`, `TIRED`, and `HUNGARY`.

## Week 7: Ask DeepSeek From Laptop

Set your DeepSeek API key and the board URL in your terminal:

```sh
export DEEPSEEK_API_KEY="your_api_key_here"
export BOT_URL="http://192.168.1.123"
```

`BOT_URL` can also be just the IP, like `192.168.1.123`; the script will add `http://`.

Then ask the bot. DeepSeek will choose both the reply text and face state:

```sh
python3 tools/ask_bot.py "say hello in one short sentence"
```

The helper now asks DeepSeek for:

- `screen_text`: short ASCII text for the T-RGB bubble.
- `speech_text`: short Chinese-first TTS text for the laptop speaker.
- `memory_candidate`: an optional note worth keeping for later memory consolidation.

DeepSeek can now choose from the companion-oriented expression states above. The firmware maps those states onto the current lightweight image assets, then keeps the face alive with an ambient sequence and subtle bubble/badge motion while idle.

When `BOT_URL` is set, each reply is also appended to `/memory/moments.jsonl` on the T-RGB through `/log`.

You can still force a face state when testing:

```sh
python3 tools/ask_bot.py --state TEASING "complain about car repairs"
```

If you want voice now, use your Mac as the temporary speaker:

```sh
python3 tools/ask_bot.py --speak "say hello out loud"
```

This keeps the T-RGB doing the face/text display while macOS speaks the Chinese-first `speech_text`. Any Bluetooth speaker selected as your Mac's audio output will work.

The default macOS voice is `Tingting`. If that voice is not installed, either install a Chinese voice in macOS Accessibility settings or choose another voice:

```sh
python3 tools/ask_bot.py --speak --voice Samantha "say hello out loud"
```

## Week 12: SD Card Write Test

The next memory milestone is proving the T-RGB can write to its own SD card.

After uploading firmware, open this in your browser:

```text
http://192.168.1.123/sd-write-test
```

Expected response:

```json
{"ok":true,"path":"/memory/sd_write_test.txt","size":123}
```

Each request appends one line to:

```text
/memory/sd_write_test.txt
```

This is the small proof before building real companion memory files like `moments.jsonl`, `user_facts.json`, and `companion_self.json`.

## Week 13: Moment Log

The first real memory rail is append-only interaction logging:

```text
/memory/moments.jsonl
```

With `BOT_URL` set, `tools/ask_bot.py` writes one JSON line after each reply. You can also test the endpoint directly:

```text
http://192.168.1.123/log?event=reply&source=laptop&state=HAPPY&screen_text=Hi&speech_text=你好&memory=User%20likes%20short%20answers
```

Expected response:

```json
{"ok":true,"path":"/memory/moments.jsonl","size":456}
```

Use `--skip-memory-log` if you want to send a reply without writing a moment.

## Week 14: Personality Contract

The board exposes the current personality/state contract as JSON:

```text
http://192.168.1.123/personality
```

Use this to check which expression states the laptop-side personality prompt is allowed to choose and how the firmware is currently mapping those states to local face assets.

## Memory Second Prototype: Consolidation

The companion now supports a three-layer memory pipeline. Raw interaction moments from `/memory/moments.jsonl` are periodically consolidated into durable memory files by a laptop-side script that uses DeepSeek to summarize and extract meaning.

### Durable Memory Files

| File | Purpose |
|---|---|
| `companion_self.json` | What the companion learns about itself (traits, preferences, growth) |
| `user_facts.json` | Facts and preferences about the user |
| `shared_phrases.jsonl` | Inside jokes, recurring phrases, shared rituals |
| `boundaries.json` | User-set boundaries and companion's soft limits |
| `backstory_fragments.json` | Emerged fragments of companion origin story |

### Memory Endpoints

```text
GET  http://192.168.1.123/memory/moments.jsonl     # Download raw moments log
GET  http://192.168.1.123/memory/status             # File sizes and lock state
GET  http://192.168.1.123/memory/file?name=companion_self.json  # Read one memory file
POST http://192.168.1.123/memory/consolidate        # Receive consolidated files
```

### Run Consolidation

```sh
python3 tools/consolidate_memory.py --bot-url http://192.168.1.123
```

The script:
1. Downloads `moments.jsonl` and existing memory files from the device.
2. Sends everything to DeepSeek with a consolidation prompt.
3. POSTs the updated memory files back to the device.
4. The companion shows "排序记忆中..." (Sorting memory...) during consolidation.

Use `--reset-moments` to truncate the moments log after a successful consolidation:

```sh
python3 tools/consolidate_memory.py --bot-url http://192.168.1.123 --reset-moments
```

Test without calling DeepSeek:

```sh
python3 tools/consolidate_memory.py --bot-url http://192.168.1.123 --dry-run
```

The consolidation lock (`/memory/.consolidation_lock`) prevents concurrent consolidations. If the companion shows the lock is held, wait and retry.

## Week 15: Upload Visual Assets

The firmware exposes:

```text
POST http://192.168.1.123/upload?folder=/data
GET  http://192.168.1.123/assets?folder=/data
```

Use the laptop helper to send visual assets directly to the SD card:

```sh
python3 tools/upload_asset.py --bot-url http://192.168.1.123 --folder /data examples/lv_single_image/data/main.png --list
```

You can upload several files at once:

```sh
python3 tools/upload_asset.py --bot-url 192.168.1.123 --folder /data examples/lv_single_image/data/*.png --list
```

Or rename a single uploaded file:

```sh
python3 tools/upload_asset.py --bot-url 192.168.1.123 --folder /data ./test.gif --name memory.gif
```

Supported upload types are `.jpg`, `.jpeg`, `.png`, and `.gif`. Convert MP4 source loops to GIF before uploading. The upload endpoint creates the target folder if needed. After replacing an asset that is already on screen, send a `/say` request or reset the board to reload it.

By default, `tools/upload_asset.py` resizes `.jpg`, `.jpeg`, and `.png` stills to fit inside `128x128` before upload. The firmware zooms the lightweight image on-device. GIF uploads are accepted only below 1 MB so they can be preloaded into PSRAM instead of streamed slowly from SD.

## Week 16: Preview Visual Assets

The firmware exposes:

```text
GET http://192.168.1.123/preview?file=memory.png&text=Memory%20test
```

Use the laptop helper to show an uploaded still image immediately:

```sh
python3 tools/preview_asset.py --bot-url 192.168.1.123 memory.png --text "memory test"
```

Preview supports `.jpg`, `.jpeg`, `.png`, and `.gif`. Use `--clean` for a bare GIF playback test without the badge, Wi-Fi label, or bubble:

```sh
python3 tools/preview_asset.py --bot-url 192.168.1.123 --folder /data/gif_loops/128 --clean listen_loop.gif
```

## Week 18: Runtime Expression Binding

The firmware exposes:

```text
GET http://192.168.1.123/bind?state=PROUD&file=pround.png
GET http://192.168.1.123/bindings
```

Use the laptop helper to bind a state to an uploaded still image:

```sh
python3 tools/bind_asset.py --bot-url 192.168.1.123 PROUD pround.png
python3 tools/bind_asset.py --bot-url 192.168.1.123 MEMORY memory.png
python3 tools/bind_asset.py --bot-url 192.168.1.123 --list
```

Bindings are saved to `/memory/face_bindings.csv` on the SD card and loaded at boot. Use `--reset` to return a state to its firmware default:

```sh
python3 tools/bind_asset.py --bot-url 192.168.1.123 PROUD --reset
```

## Week 19: Animated GIF Expressions

Runtime bindings and previews support `.gif` assets. Upload a GIF, bind it to a state, and `/say` will render it as an animated loop:

```sh
python3 tools/upload_asset.py --bot-url 192.168.1.123 --folder /data/gif_loops/128 ./teasing.gif --list
python3 tools/bind_asset.py --bot-url 192.168.1.123 --folder /data/gif_loops/128 TEASING teasing.gif
python3 tools/ask_bot.py --mock --bot-url 192.168.1.123 --state TEASING --skip-memory-log "gif test"
```

Use 128x128 GIFs under 1 MB. The upload helper does not resize GIFs; convert them before upload.

## Week 20: Convert MP4 Loops To GIF

The T-RGB firmware does not play MP4. Convert MP4 loops to small GIFs with `ffmpeg`:

```sh
python3 tools/convert_mp4_loops.py examples/lv_single_image/data/*_loop.mp4
python3 tools/upload_asset.py --bot-url 192.168.1.123 --folder /data/gif_loops/128 examples/lv_single_image/data/gif_loops/128/*.gif --no-resize
```

The default conversion matches the current board-friendly format: `128px`, about `16.7 fps`, up to `3 seconds`, and `256` colors. Keep generated GIFs below 1 MB. You can adjust the conversion when testing:

```sh
python3 tools/convert_mp4_loops.py examples/lv_single_image/data/teasing_loop.mp4 --size 128 --fps 12 --duration 2 --colors 128
```

Validate the local board asset folder before upload:

```sh
python3 .agents/skills/t-rgb-asset-pipeline/scripts/check_t_rgb_assets.py
```

For smoother playback, prefer shorter or fewer-frame 128px GIFs over larger/full-frame loops. Large GIFs are decoded in software and can feel laggy on the ESP32-S3.

## Procedural Eye Assets

For a simpler robot-screen look, generate low-detail pixel-eye PNG/GIF assets instead of AI-rendered character art.
The current T-RGB-friendly target is a fast 5-frame GIF loop: 128x128, 16 colors, about 60 ms per frame, and under 6 KB per state.

```sh
python3 tools/generate_eye_assets.py
```

This writes the current display-safe set:

```text
examples/lv_single_image/data/eye_assets_perf_fast/128x128/
```

Upload and bind the fast loops with:

```sh
python3 tools/generate_eye_assets.py
python3 tools/upload_asset.py --bot-url 192.168.1.123 --folder /data/gif_loops/128_5f_fast examples/lv_single_image/data/eye_assets_perf_fast/128x128/*_loop.gif --no-resize --list
python3 tools/bind_asset.py --bot-url 192.168.1.123 --folder /data/gif_loops/128_5f_fast IDLE idle_loop.gif
```

Keep animations tiny: blink, eye position, brightness pulse, and subtle mouth motion. Avoid full-screen video, large GIFs, and high-color gradients when testing on ESP32.

The generated states intentionally use distinct readable cues:

- `listening`: a side receiver dish with small wave pulses.
- `thinking`: a tiny antenna and soft particles.
- `speaking`: pulsing eyes and a small mouth.
- `teasing`: a wink, small smile, and sparkle.
- `annoyed`: compressed eyes, sharp brows, and a tiny shake.
- `proud`: bright confident eyes, lifted brows, and a small smile.
- `sleepy`: dim eyes with a floating `Z`.
- `memory`: closed eyes, antenna pulse, and memory particles.
- `uncertain`: asymmetric eyes plus a small sweat drop.

The default generator writes only static PNG anchors, `*_loop.gif` files, and `contact_sheet.png`. Use `--with-transitions` only for experiments; transition clips are not part of the final fast T-RGB asset set.

By default, the script uses `deepseek-v4-flash`. To use another DeepSeek model:

```sh
export DEEPSEEK_MODEL="deepseek-v4-pro"
```

Test without calling DeepSeek or the board:

```sh
python3 tools/ask_bot.py --mock --dry-run --bot-url http://192.168.1.123 "hello"
```

If the script times out while sending to the T-RGB, first test the board itself:

```sh
python3 tools/ask_bot.py --mock --bot-url http://192.168.1.123 "hello"
```

If that also times out, open `http://192.168.1.123/` in your browser. Use the IP currently shown on the LilyGo screen; it can change after reconnecting to Wi-Fi.

## Common Failures

- `SD card not found`: reinsert the SD card and reset the board.
- `Missing slideshow image`: check the `/data/*.jpg` filenames on the SD card.
- `Wi-Fi: connection failed`: check `wifi_config.h`, then reset the board.
- Laptop cannot reach the board: make sure laptop and T-RGB are on the same Wi-Fi.
- `T-RGB request timed out`: update `BOT_URL` to the IP currently shown on the board, or reset the board if the screen/server looks stuck.
- Square boxes in text: the laptop script converts DeepSeek's Unicode punctuation to screen-safe ASCII before sending.
- Wrong expression: pass `--state HAPPY`, `--state MAD`, etc. to override the AI's chosen state.
- No external speaker from T-RGB: the T-RGB docs say the Grove port is I2C/shared with touch and there are no free GPIO pins, so use `--speak` on the laptop for now.
- SD write test fails: check the SD card is inserted, not write-locked, and formatted so the board can mount it.
- Moment log fails: open `http://BOARD_IP/sd-write-test` first. If that works, retry with shorter text because `/log` uses a URL query string.
- Script says `Missing DEEPSEEK_API_KEY`: export the key in the same terminal before running the script.
