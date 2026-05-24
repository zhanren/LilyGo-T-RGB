---
stepsCompleted: [1, 2]
inputDocuments: []
session_topic: 'Build a LilyGo T-RGB AI companion bot inspired by XiaoZhi ESP32-style voice assistants'
session_goals: 'Create a beginner-friendly, gradual plan from zero hardware and C++ knowledge toward voice input, camera/photo or video input, AI reasoning, persona, and voice output'
selected_approach: 'progressive-flow'
techniques_used: ['Question Storming', 'Mind Mapping', 'First Principles Thinking', 'Decision Tree Mapping']
ideas_generated: []
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** Mary
**Date:** 2026-05-14

## Session Overview

**Topic:** Build a LilyGo T-RGB AI companion bot inspired by XiaoZhi ESP32-style voice assistants.

**Goals:** Create a beginner-friendly, gradual plan from square zero toward a working interactive bot that can take voice input, use camera/photo or video context, send data to an AI model, respond with a defined persona, and output spoken audio.

### Context Guidance

No separate context file was provided. The user has already purchased the core components: LilyGo T-RGB, camera module, microphone module, battery, glue gun, and soldering iron kit. The user is new to C++ and hardware, so the plan must emphasize staged learning, safety, wiring basics, firmware basics, and incremental prototypes before full integration.

### Session Setup

The inspiration is closer to a XiaoZhi ESP32-style AI voice assistant than a generic chatbot. The brainstorming should produce a practical roadmap with learning milestones, build checkpoints, risk reduction steps, and clear definitions of "done" at each stage.

## Technique Selection

**Approach:** Progressive Technique Flow
**Journey Design:** Systematic development from exploration to action.

**Progressive Techniques:**

- **Phase 1 - Exploration:** Question Storming for surfacing unknowns, dependencies, fears, and decisions before solving too early.
- **Phase 2 - Pattern Recognition:** Mind Mapping for grouping the project into learning tracks, hardware modules, firmware modules, AI services, and build milestones.
- **Phase 3 - Development:** First Principles Thinking for reducing the bot to fundamental capabilities and staging prototypes from easiest to hardest.
- **Phase 4 - Action Planning:** Decision Tree Mapping for turning the staged strategy into concrete choices, checkpoints, and next actions.

**Journey Rationale:** The user is starting from square zero in hardware and C++, while aiming for a multi-modal AI bot with voice, camera, persona, and spoken output. The journey should first expose the full problem space, then compress it into an approachable path with increasing complexity.

## Technique Execution Results

**Question Storming - Phase 1 Exploration**

**Initial uncertainty pillars from user:**

- Understanding the LilyGo T-RGB board.
- Wiring, soldering, and battery power.
- C++ and firmware development.

**User-ranked intimidation order:**

1. LilyGo board basics.
2. Wiring, soldering, and battery safety.
3. C++ and firmware.
4. Full AI voice and vision architecture.

**Current capability baseline:**

- User can already mostly upload code using official seller examples.
- User can display simple GIFs or text.
- User is still struggling with showing pictures on the screen.
- Wi-Fi, microphone input, camera/photo capture, AI request/response, and spoken output remain important milestones.

**Repo observations:**

- The project includes examples for hello world, GIF, image decoding, touchpad, battery voltage, backlight, QR code, LVGL UI, and factory demos.
- `examples/lv_images/lv_images.ino` displays JPG images from an SD card using LVGL image decoding.
- README identifies the board family as ESP32-S3R8 with 16 MB flash and 8 MB PSRAM, 480x480 display.
- README warns that the Grove port is I2C shared with touch and that the T-RGB has no free GPIO and cannot be expanded. This may constrain direct camera/microphone attachment and should be treated as a major architecture question.

**User-provided component evidence:**

- Microphone appears to be an INMP441 I2S MEMS microphone module.
- Speaker amplifier appears to be a MAX98357A I2S Class D amplifier/DAC breakout.
- Both audio modules imply an I2S audio path: microphone input over I2S and speaker output through I2S amplifier.
- Direct attachment to the T-RGB remains uncertain because the board documentation warns about limited/no free GPIO.
- Camera is labeled as a Treedix OV2640 mini camera module.
- OV2640 camera integration should be treated as a many-pin camera-interface problem, not a simple two-wire I2C sensor module. It likely belongs on an ESP32-CAM-style board or a dedicated ESP32-S3 camera-capable board before attempting any integration with the T-RGB.

**Motivating demo preference:**

- Near-term confidence demo: type to AI on a computer and have the T-RGB display the answer.
- Long-term north star: full dream demo with microphone, camera, AI, voice output, and screen.

**Phase 1 completion note:**

- Question Storming generated 100+ questions/unknowns across board basics, display, wiring, C++ firmware, Wi-Fi, I2S audio, OV2640 camera integration, AI architecture, persona, and learning cadence.
- User chose to move to Phase 2 Mind Mapping.

**Mind Mapping - Phase 2 Pattern Recognition**

**Central concept:** AI Companion Bot.

**Primary branches:**

1. T-RGB Display Body: screen, LVGL, images, face, text bubbles, touch, battery status.
2. Firmware Basics: C++ basics, PlatformIO, upload/debug loop, Serial Monitor, libraries.
3. Wi-Fi Bridge: connect T-RGB to network, receive messages, HTTP/WebSocket/MQTT.
4. AI Brain: laptop server, cloud AI API, persona prompt, memory, response formatting.
5. Audio System: INMP441 mic, MAX98357A amp, speaker, I2S, speech-to-text, text-to-speech.
6. Vision System: OV2640 camera, ESP32-CAM/camera-ready board, photo capture, image upload.
7. Bot Experience: name, personality, face states, thinking animation, response style.
8. Physical Build: enclosure, battery, wiring, soldering, glue, mounting.
9. Safety and Debugging: power checks, pin mapping, short prevention, rollback examples.

**Beginner-safe dependency order accepted by user:**

1. Display Body.
2. Firmware Basics.
3. Wi-Fi Bridge.
4. AI Brain.
5. Bot Experience.
6. Audio System.
7. Vision System.
8. Integration.
9. Physical Build.

**Key pattern:** Do not wire the final bot first. Prototype each sense separately, then integrate.

**First Principles Thinking - Phase 3 Idea Development**

**Fundamental bot loop:** Input -> Understanding -> Personality -> Output.

**Final version target:**

- Input: voice plus camera/photo/video.
- Understanding: AI model processes audio, text, and image/video context.
- Personality: prompt, memory, tone, and emotional state.
- Output: voice plus face plus screen text.

**First working version:**

- Input: typed text on computer.
- Understanding: AI API on laptop.
- Personality: system prompt.
- Output: T-RGB displays AI answer.

**Prototype ladder:**

- P0: Restore official examples to prove board and toolchain.
- P1: Display still image on T-RGB to solve current display struggle.
- P2: Animated face plus text bubble to make the bot visually alive.
- P3: Wi-Fi text receiver so computer can control T-RGB.
- P4: Laptop AI sends response to T-RGB for first real AI bot demo.
- P5: Persona plus expression mapping so the bot feels like a character.
- P6: Separate I2S audio test to prove mic/speaker path.
- P7: Separate camera test to prove OV2640 path.
- P8: Audio/vision connect to laptop AI so multimodal brain works.
- P9: Integrated physical bot with enclosure and battery.

**First-principles decision:** The T-RGB does not need to be the whole bot. It can be the face.

**Learning preference:** User prefers project-first learning, where each week has one build goal and learning is attached to that goal.

**Decision Tree Mapping - Phase 4 Action Planning**

**Core decisions:**

1. Can the T-RGB display still images reliably?
   - If yes: move to animated face and UI states.
   - If no: solve image pipeline first: file format, SD card path, LVGL version, image size.
2. Can the T-RGB connect to Wi-Fi and receive text?
   - If yes: build laptop-to-T-RGB message bridge.
   - If no: learn ESP32 Wi-Fi examples separately.
3. Can laptop call AI and send response to T-RGB?
   - If yes: first AI bot demo achieved.
   - If no: debug laptop server/API before adding more hardware.
4. Can T-RGB handle audio/camera directly?
   - Likely no or painful because of GPIO constraints.
   - Therefore: test audio and camera on separate boards/modules first.
5. Is the distributed bot working?
   - T-RGB face receives commands.
   - Audio board handles voice.
   - Camera board handles image.
   - Laptop/cloud AI coordinates.
6. Only after distributed prototype works: physical build with battery, enclosure, soldering, mounting, cable strain relief, and heat/glue placement.

**Schedule constraint:** User selected 5-7 hours per week.

**Accepted project-first roadmap:**

### Phase 1: Make The T-RGB Feel Alive

| Week | Goal | Done When |
|---|---|---|
| 1 | Run and understand seller examples | User can upload, monitor logs, and switch examples |
| 2 | Display user's own still image | A custom JPG/PNG appears correctly on screen |
| 3 | Build a simple bot face | Face has idle, happy, thinking, and confused states |
| 4 | Add text bubble UI | T-RGB can show a short message cleanly |

### Phase 2: First AI Bot Demo

| Week | Goal | Done When |
|---|---|---|
| 5 | Connect T-RGB to Wi-Fi | Serial monitor shows connected IP |
| 6 | Send text from laptop to T-RGB | Laptop command changes screen text |
| 7 | Laptop calls AI, sends result to T-RGB | User types on laptop and AI answer appears on bot |
| 8 | Add persona plus expression tags | AI response changes both text and face |

### Phase 3: Add Senses Separately

| Week | Goal | Done When |
|---|---|---|
| 9 | Test MAX98357A speaker output separately | Speaker plays a tone or WAV |
| 10 | Test INMP441 microphone separately | User can detect or record voice samples |
| 11 | Test OV2640 camera separately | Camera captures one photo successfully |
| 12 | Send audio/photo to laptop AI | AI responds based on voice or image |

### Phase 4: Integrate

| Week | Goal | Done When |
|---|---|---|
| 13 | T-RGB displays AI reactions from audio input | Speech input produces screen response |
| 14 | T-RGB reacts to camera description | Photo -> AI description -> bot expression |
| 15 | Add spoken response | AI answer is played through speaker path |
| 16 | Physical assembly plan | Soldering, mounting, battery, and enclosure are planned after subsystem proof |

**Roadmap principle:** No final soldered build until each subsystem works alone.

**Immediate next milestone:** Week 2, display user's own still image on the T-RGB.

**Week 2 implementation start:**

- Added `examples/lv_single_image` as a focused single-image display milestone.
- Configured PlatformIO to build `examples/lv_single_image` by default.
- Build verification succeeded with PlatformIO.

**Week 2 completion:**

- User successfully displayed the dog/custom picture on the LilyGo T-RGB screen.
- User confirmed the board can read a JPG from SD card and render it through LVGL.
- Extended the working example into a slideshow that reads images from `/data/image_5.jpg` through `/data/image_11.jpg` on the SD card.
- Converted the active example from `.ino` to `main.cpp` so PlatformIO builds it reliably.
- PlatformIO build verification succeeded after the slideshow update.

**Next milestone started:** Week 3, build a simple bot face with named states using existing `/data` images as placeholder expressions.

**Week 3 implementation start:**

- Updated the active firmware to use named bot face states instead of anonymous slideshow images.
- Current states use resized 480x480 JPG assets:
  - `IDLE` -> `/data/main.jpg`
  - `HAPPY` -> `/data/thumb_up.jpg`
  - `DISTRACTED` -> `/data/distracting.jpg`
  - `MAD` -> `/data/mad.jpg`
  - `TIRED` -> `/data/tired.jpg`
  - `HUNGARY` -> `/data/hungary.jpg`
- The firmware cycles states every 3 seconds and displays the state name/caption on screen.
- PlatformIO build verification succeeded.

**Week 3 completion:**

- User confirmed the state images render correctly after switching from large PNG files to 480x480 JPG files.
- Simple bot face state milestone is complete.

**Next milestone started:** Week 4, add a text bubble UI so the T-RGB can show a short message cleanly.

**Week 4 implementation start:**

- Added a top state badge for the active bot state.
- Added a rounded bottom text bubble for the state's short message.
- Existing face states continue to cycle automatically every 3 seconds.
- PlatformIO build verification succeeded.

**Week 4 completion:**

- User confirmed the face state UI with text bubble works.
- Text bubble milestone is complete.

**Next milestone started:** Week 5, connect T-RGB to Wi-Fi and show the connected IP address.

**Week 5 implementation start:**

- Added optional local `wifi_config.h` support for Wi-Fi SSID/password.
- Added `wifi_config.example.h` template.
- Added `.gitignore` entry so `wifi_config.h` stays local and private.
- Firmware shows Wi-Fi status on screen and in Serial Monitor.
- If Wi-Fi connects, the screen displays the board IP address.
- PlatformIO build verification succeeded.

**Week 5 completion:**

- User confirmed Wi-Fi connection works.
- T-RGB displays its connected IP address.
- Wi-Fi milestone is complete.

**Next milestone started:** Week 6, send text from laptop to T-RGB over Wi-Fi.

**Week 6 implementation start:**

- Added a tiny HTTP server on port 80.
- Added `GET /` help text endpoint.
- Added `GET /say?text=...&state=...` endpoint to update the bot text bubble and optional face state.
- Supported states: `IDLE`, `HAPPY`, `DISTRACTED`, `MAD`, `TIRED`, `HUNGARY`.
- Remote messages pause automatic face cycling for 15 seconds.
- PlatformIO build verification succeeded.

**Week 6 completion:**

- User confirmed laptop-to-T-RGB text works.
- The board can receive text over Wi-Fi and update the on-screen face/message.

**Next milestone started:** Week 7, laptop calls AI and sends the result to T-RGB.

**Week 7 implementation start:**

- Added `tools/ask_bot.py` as the laptop bridge.
- Initial bridge used OpenAI Responses API; the current bridge now uses DeepSeek after the provider update below.
- Added `--mock` and `--dry-run` modes for safe local testing.
- Updated the active milestone README with SD card, Wi-Fi, HTTP, and AI bridge instructions.

**Week 7 provider update:**

- Converted `tools/ask_bot.py` from OpenAI Responses API to DeepSeek Chat Completions API.
- The script now reads `DEEPSEEK_API_KEY`, defaults to `deepseek-v4-flash`, and supports `DEEPSEEK_MODEL` for switching models.

**Week 7 timeout troubleshooting update:**

- User hit `T-RGB request failed: timed out`, meaning the AI call completed but the laptop could not reach the board HTTP server.
- Updated `tools/ask_bot.py` to check `BOT_URL/` before calling DeepSeek, print the AI answer before sending to the board, and provide clearer timeout guidance.

**Week 7 display text cleanup update:**

- User saw square boxes for punctuation-like characters on the T-RGB screen.
- Updated `tools/ask_bot.py` to request plain ASCII from DeepSeek and sanitize outgoing text by converting common Unicode punctuation to ASCII before sending it to `/say`.

**Week 8 implementation start:**

- Updated `tools/ask_bot.py` so DeepSeek returns structured JSON with both `state` and `text`.
- The script now defaults to `--state AUTO`, allowing the AI to choose one of `IDLE`, `HAPPY`, `DISTRACTED`, `MAD`, `TIRED`, or `HUNGARY`.
- Users can still force an expression with `--state HAPPY`, `--state MAD`, etc.

**Week 9 direction update:**

- The T-RGB repo notes that the Grove port is I2C/shared with touch and that T-RGB has no free GPIO, so directly wiring MAX98357A I2S audio to this board is not a good next step.
- Added laptop-side voice output to `tools/ask_bot.py` with `--speak`, using macOS `say` as a temporary speaker path while the T-RGB continues to show face/text.

**Week 8 completion:**

- User confirmed AI expression auto-selection works.
- Persona + expression mapping milestone is complete.

---

**Week 9 hardware reality check:**

- Completed full T-RGB GPIO audit. Result: **zero free GPIO pins.**
- Every GPIO (0-48) is consumed by the 18-pin RGB display bus, SD card, touch controller, I2C expander, backlight, and boot button.
- The Grove port is I2C-only, shared with the touch controller — cannot be repurposed for I2S or GPIO.
- README confirms: "T-RGB has no free GPIO and cannot be expanded."
- **Conclusion:** The T-RGB cannot directly connect the MAX98357A speaker amp, INMP441 microphone, or OV2640 camera.

**Week 9 pivot — Bluetooth TTS (no new hardware):**

- Added `--speak` flag to `tools/ask_bot.py`.
- Uses macOS built-in `say` command for text-to-speech.
- Voice defaults to **Samantha** (high-quality en_US voice), configurable via `--voice` or `BOT_VOICE` env var.
- Audio outputs through whatever audio device macOS is set to — including **Bluetooth speakers/headphones**.
- Zero new hardware required. The bot now has a voice through the laptop.
- Usage: `python3 tools/ask_bot.py "are you hungry" --speak`

**Week 9 pivot — Revised project roadmap (no camera/mic hardware):**

Given zero free GPIO on T-RGB and no second ESP32 board, the project pivots to a **T-RGB + Laptop** architecture where:

- **T-RGB** = expressive face (display, touch input, Wi-Fi)
- **Laptop** = AI brain (DeepSeek) + voice output (macOS `say` → Bluetooth speaker)
- **Touch** = new input modality (T-RGB has a GT911/CST820/FT3267 touch panel — already initialized)

**Untapped T-RGB capabilities (no extra hardware):**

| Capability | Built In? | Status |
|---|---|---|
| 🖼️ Image display | ✅ | Weeks 1-2 complete |
| 😀 Face states (6 expressions) | ✅ | Weeks 3-4 complete |
| 📶 Wi-Fi HTTP server | ✅ | Weeks 5-6 complete |
| 🤖 AI text responses via laptop | ✅ | Weeks 7-8 complete |
| 🔊 Voice output via laptop TTS | ✅ | Week 9 — just added |
| 👆 **Touch interaction** | ✅ GT911/CST820/FT3267 | **Not yet used** |
| 🌡️ **Battery voltage** | ✅ ADC on GPIO4 | Example exists, not in bot |
| 📊 **Animated transitions** | ✅ LVGL | Not yet built |
| 🧠 **Conversation memory** | ❌ Laptop-side (Python) | Not yet built |
| 🌐 **Web dashboard** | ❌ Laptop-side | Not yet built |
| 📷 Camera input | ❌ Needs ESP32-CAM | Deferred |
| 🎤 Microphone input | ❌ Needs ESP32 board | Deferred |

**Revised Phase 3 roadmap (Laptop-enhanced bot):**

| Week | Goal | Done When |
|---|---|---|
| 9 | Add voice output via laptop TTS | Bot speaks AI replies through Mac/Bluetooth speaker |
| 10 | Touch interaction | Tapping screen triggers bot responses |
| 11 | Touch + face interaction | Tap face to change mood, double-tap to ask bot |
| 12 | Conversation memory | Bot remembers last 5 exchanges |
| 13 | Animated transitions | Face smoothly crossfades between states |
| 14 | Web dashboard | Browser page showing bot status, conversation log |
| 15 | Battery status on face | Low battery warning on screen |

**Audio/camera hardware deferred to future when second ESP32 board is acquired.**

**Immediate next milestone:** Week 10, touch interaction — use the T-RGB's built-in touch panel as input.<｜end▁of▁thinking｜>

**Week 10 implementation start:**

- Updated the active `examples/lv_single_image/main.cpp` firmware to poll the built-in touch panel with `panel.getPoint(&x, &y)`.
- Single tap cycles to the next face state and briefly pauses automatic cycling.
- Double tap shows a special happy reaction.
- Touch coordinates print to Serial Monitor, and a small white dot flashes at the detected touch location.
- Updated the active README with touch interaction instructions and troubleshooting.

**Week 10 double-tap tuning:**

- User reported double tap did not show the happy reaction.
- Widened the double-tap window from 500 ms to 800 ms.
- Changed detection to trigger double-tap on the second touch-down instead of waiting for the second release, which should better match how the T-RGB touch controller reports taps.

**Week 11 implementation start:**

- Added `GET /touch` endpoint to the T-RGB firmware.
- The endpoint returns the latest touch event as JSON: event id, type, x/y coordinates, and board uptime milliseconds.
- Single tap records `tap`; double tap records `double_tap`.
- Added `--watch-touch` mode to `tools/ask_bot.py`.
- In watch mode, the laptop polls `/touch`; a `double_tap` event triggers a DeepSeek prompt, sends the AI reply back to `/say`, and can speak it with `--speak`.

**Week 11 URL handling fix:**

- User hit `ValueError: unknown url type` when `BOT_URL` was set to `192.168.1.138` without `http://`.
- Updated `tools/ask_bot.py` so bare IP addresses automatically become `http://IP`.
- Added friendlier malformed URL errors instead of Python tracebacks.

**Week 11 touch trigger tuning:**

- User reported double-tapping did not appear to trigger anything in watch mode.
- Changed `--watch-touch` default trigger from double-tap only to `any` touch event.
- Added `--touch-trigger tap|double_tap|any` so double-tap can still be required later.
- Watch mode now prints the initial `/touch` state and flushes touch event logs immediately.

**Week 11 immediate touch-down event fix:**

- User confirmed the screen shows a white dot on touch, but Python did not record events.
- Updated firmware to record a `touch_down` event immediately when the white dot appears.
- Updated Python `--watch-touch` default trigger to `touch_down`, with `--touch-trigger touch_down|tap|double_tap|any`.

**Week 12 direction change: SD card write proof**

- User asked to dial back touch work for now and follow the newer 2026-05-23 brainstorm around local SD-card memory.
- Added `/sd-write-test` endpoint to prove the T-RGB can create `/memory`, append to `/memory/sd_write_test.txt`, and read back file size.
- This becomes the first practical step toward append-only local memory logs.
