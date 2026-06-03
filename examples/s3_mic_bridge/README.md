# S3-N16R8 Microphone Bridge

This is the first sensor-side firmware for the separate ESP32-S3-N16R8 board. It reads an I2S microphone and prints live audio levels over USB serial. If Wi-Fi and the T-RGB URL are configured, it can also notify the T-RGB display through the existing `/say` endpoint.

Keep the T-RGB and the S3 sensor board powered by USB-C while prototyping. Do not power the S3 board or microphone from the T-RGB `3V3` pin.

## Hardware

Tested target board configuration:

- ESP32-S3-N16R8 USB-C development board
- 16 MB flash
- 8 MB OPI PSRAM
- WCH USB serial adapter for upload and Serial Monitor
- Arduino framework through PlatformIO

Recommended first microphone:

- INMP441 I2S microphone module
- SPH0645-style I2S microphones should also work, though the active channel may need changing in `mic_config.h`.

## Wiring

Default firmware pins:

| Mic Module | S3-N16R8 |
| --- | --- |
| VDD | 3V3 |
| GND | GND |
| SCK / BCLK | GPIO4 |
| WS / LRCLK | GPIO5 |
| SD / DOUT | GPIO6 |
| L/R | GND |

The L/R-to-GND wiring is for left-channel INMP441 modules. If your module is wired to the right channel, copy `src/mic_config.example.h` to `src/mic_config.h` and change:

```cpp
#define MIC_I2S_CHANNEL_FORMAT I2S_CHANNEL_FMT_ONLY_RIGHT
```

Avoid GPIO19 and GPIO20 because they are USB D-/D+ on ESP32-S3 USB-C boards. Avoid GPIO0, GPIO45, and GPIO46 for first tests because they are boot-strapping pins on many ESP32-S3 boards.

## Build And Upload

From this folder:

```sh
platformio run -e hosyond-s3-n16r8-mic
platformio run -e hosyond-s3-n16r8-mic -t upload
platformio device monitor -b 115200
```

Expected serial output:

```text
S3-N16R8 microphone bridge
I2S pins: BCLK=4 WS=5 DATA=6
Sample rate: 16000 Hz
Mic setup OK. Speak near the mic and watch the level.
  -42.3 dBFS [#############...................]
```

If the numbers stay near `-120.0 dBFS`, check `VDD`, `GND`, `SD/DOUT`, and whether the microphone is on the left or right channel.

## Optional T-RGB Notification

After the serial mic test works, copy the config file:

```sh
cp src/mic_config.example.h src/mic_config.h
```

Then fill in:

```cpp
#define WIFI_SSID "Your WiFi Name"
#define WIFI_PASSWORD "Your WiFi Password"
#define T_RGB_BOT_URL "http://192.168.1.123"
```

When the mic level crosses `VOICE_TRIGGER_DBFS`, the S3 board calls:

```text
/say?state=LISTENING&text=Mic%20heard%20you...
```

That keeps the architecture clean:

```text
I2S mic -> S3-N16R8 sensor bridge -> Wi-Fi HTTP -> T-RGB face display
```
