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
- Week 15: upload JPG, PNG, GIF, and MP4 visual assets to a chosen SD card folder over Wi-Fi.
- Week 16: preview any uploaded JPG, PNG, or GIF on the display without reflashing firmware.
- Week 17: resize JPG/PNG stills during upload so large generated assets stay display-safe.
- Week 18: bind expression states to uploaded still assets at runtime and persist the mapping on the SD card.
- Week 19: render uploaded GIF loops for animated expression states.
- Week 20: convert MP4 expression loops to small GIFs with `ffmpeg` for smoother T-RGB testing.

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
python3 tools/upload_asset.py --bot-url 192.168.1.123 --folder /data examples/lv_single_image/data/*.png examples/lv_single_image/data/*.mp4 --list
```

Or rename a single uploaded file:

```sh
python3 tools/upload_asset.py --bot-url 192.168.1.123 --folder /data ./test.gif --name memory.gif
```

Supported upload types are `.jpg`, `.jpeg`, `.png`, `.gif`, and `.mp4`. The current sketch displays JPG, PNG, and GIF assets through LVGL; MP4 files are stored on the SD card for asset iteration but are not played by this firmware yet. The upload endpoint creates the target folder if needed. After replacing an asset that is already on screen, send a `/say` request or reset the board to reload it.

By default, `tools/upload_asset.py` resizes `.jpg`, `.jpeg`, and `.png` stills to fit inside `480x480` before upload. This keeps large generated assets from overwhelming the T-RGB image decoder. Use `--resize-max 360` for smaller files, or `--no-resize` when you intentionally want to upload the original file unchanged.

## Week 16: Preview Visual Assets

The firmware exposes:

```text
GET http://192.168.1.123/preview?file=memory.png&text=Memory%20test
```

Use the laptop helper to show an uploaded still image immediately:

```sh
python3 tools/preview_asset.py --bot-url 192.168.1.123 memory.png --text "memory test"
```

Preview supports `.jpg`, `.jpeg`, `.png`, and `.gif`. MP4 files can be stored on the SD card, but this firmware does not play them yet.

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
python3 tools/upload_asset.py --bot-url 192.168.1.123 --folder /data ./teasing.gif --list
python3 tools/bind_asset.py --bot-url 192.168.1.123 TEASING teasing.gif
python3 tools/ask_bot.py --mock --bot-url 192.168.1.123 --state TEASING --skip-memory-log "gif test"
```

Use small, display-sized GIFs for now. The upload helper does not resize GIFs, and MP4 files are still stored only, not played by this firmware.

## Week 20: Convert MP4 Loops To GIF

The T-RGB firmware does not play MP4. Convert MP4 loops to small GIFs with `ffmpeg`:

```sh
python3 tools/convert_mp4_loops.py examples/lv_single_image/data/*_loop.mp4
python3 tools/upload_asset.py --bot-url 192.168.1.123 --folder /data/gif_loops examples/lv_single_image/data/gif_loops/*.gif --no-resize
```

The default conversion is intentionally conservative: `240px`, `6 fps`, `2 seconds`, and `64` colors. This keeps GIFs closer to a few hundred KB instead of multi-MB. You can adjust the conversion when testing:

```sh
python3 tools/convert_mp4_loops.py examples/lv_single_image/data/teasing_loop.mp4 --size 320 --fps 8 --duration 2
```

For smoother playback, prefer smaller GIFs over larger/full-frame loops. Large GIFs are decoded in software and can feel laggy on the ESP32-S3.

For a full-size but still compressed experiment, keep `480px` and reduce duration/colors before raising FPS:

```sh
python3 tools/convert_mp4_loops.py examples/lv_single_image/data/listen_loop.mp4 --size 480 --fps 12 --duration 2 --colors 32
```

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
