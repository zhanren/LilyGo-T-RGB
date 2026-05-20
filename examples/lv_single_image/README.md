# LV Single Image Bot Milestones

This is the active LilyGo T-RGB bot-face sketch. It displays face-state images from the SD card, connects to Wi-Fi, and accepts text from your laptop over HTTP.

## Current Milestones

- Week 2: show a custom image from SD card.
- Week 3: cycle named face states.
- Week 4: show a bottom text bubble.
- Week 5: connect to Wi-Fi and show the board IP.
- Week 6: receive laptop text at `/say`.
- Week 7: laptop script asks DeepSeek, then sends the answer to `/say`.

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

Then ask the bot. DeepSeek will choose both the reply text and face state:

```sh
python3 tools/ask_bot.py "say hello in one short sentence"
```

You can still force a face state when testing:

```sh
python3 tools/ask_bot.py --state MAD "complain about car repairs"
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
- Script says `Missing DEEPSEEK_API_KEY`: export the key in the same terminal before running the script.
