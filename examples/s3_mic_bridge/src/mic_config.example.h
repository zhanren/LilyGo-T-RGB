#pragma once

// Copy this file to mic_config.h and adjust the pins to match your wiring.
// These defaults avoid USB pins and common ESP32-S3 boot strapping pins.

#define MIC_I2S_BCLK_PIN 4
#define MIC_I2S_WS_PIN 5
#define MIC_I2S_DATA_PIN 6

#define MIC_SAMPLE_RATE 16000
#define MIC_READ_SAMPLES 512

// INMP441 with L/R tied to GND usually appears on the left channel.
#define MIC_I2S_CHANNEL_FORMAT I2S_CHANNEL_FMT_ONLY_LEFT

// Optional Wi-Fi bridge back to the T-RGB. Leave empty for serial-only mic tests.
#define WIFI_SSID ""
#define WIFI_PASSWORD ""
#define T_RGB_BOT_URL ""

// Voice activity threshold in dBFS. Raise this if normal room noise triggers it.
#define VOICE_TRIGGER_DBFS -35.0
#define VOICE_NOTIFY_COOLDOWN_MS 4000
