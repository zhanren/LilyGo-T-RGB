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

## SD Card Files

Copy the contents of `examples/lv_images/data` to the SD card so the board has:

```text
/data/main.jpg
/data/thumb_up.jpg
/data/distracting.jpg
/data/mad.jpg
/data/tired.jpg
/data/hungary.jpg
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

Supported states are `IDLE`, `HAPPY`, `DISTRACTED`, `MAD`, `TIRED`, and `HUNGARY`.

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

When `BOT_URL` is set, each reply is also appended to `/memory/moments.jsonl` on the T-RGB through `/log`.

You can still force a face state when testing:

```sh
python3 tools/ask_bot.py --state MAD "complain about car repairs"
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
