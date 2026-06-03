#include <Arduino.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <driver/i2s.h>
#include <math.h>

#if __has_include("mic_config.h")
#include "mic_config.h"
#else
#include "mic_config.example.h"
#endif

#define I2S_MIC_PORT I2S_NUM_0

static int32_t samples[MIC_READ_SAMPLES];
static unsigned long last_notify_ms = 0;
static bool wifi_started = false;

String urlEncode(const String &value)
{
    String encoded = "";
    const char *hex = "0123456789ABCDEF";

    for (size_t i = 0; i < value.length(); i++) {
        char c = value.charAt(i);
        if (isalnum((unsigned char)c) || c == '-' || c == '_' || c == '.' || c == '~') {
            encoded += c;
        } else if (c == ' ') {
            encoded += "%20";
        } else {
            encoded += '%';
            encoded += hex[(c >> 4) & 0x0F];
            encoded += hex[c & 0x0F];
        }
    }

    return encoded;
}

String levelBar(double dbfs)
{
    const int width = 32;
    int filled = (int)((dbfs + 70.0) * width / 70.0);
    filled = constrain(filled, 0, width);

    String bar = "[";
    for (int i = 0; i < width; i++) {
        bar += i < filled ? '#' : '.';
    }
    bar += "]";
    return bar;
}

void connectWifiIfConfigured()
{
    if (String(WIFI_SSID).length() == 0 || wifi_started) {
        return;
    }

    wifi_started = true;
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("Wi-Fi: connecting");

    const unsigned long start_ms = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start_ms < 12000) {
        Serial.print(".");
        delay(250);
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println();
        Serial.print("Wi-Fi: connected, IP=");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println();
        Serial.println("Wi-Fi: not connected; serial mic test will still run.");
    }
}

void notifyTRgbListening(double dbfs)
{
    if (String(T_RGB_BOT_URL).length() == 0 || WiFi.status() != WL_CONNECTED) {
        return;
    }

    if (millis() - last_notify_ms < VOICE_NOTIFY_COOLDOWN_MS) {
        return;
    }

    last_notify_ms = millis();

    String base = T_RGB_BOT_URL;
    if (!base.startsWith("http://") && !base.startsWith("https://")) {
        base = "http://" + base;
    }
    if (base.endsWith("/")) {
        base.remove(base.length() - 1);
    }

    String text = "Mic heard you: ";
    text += String(dbfs, 1);
    text += " dBFS";

    HTTPClient http;
    String url = base + "/say?state=LISTENING&text=" + urlEncode(text);
    http.begin(url);
    int code = http.GET();
    Serial.print("T-RGB notify HTTP ");
    Serial.println(code);
    http.end();
}

bool installI2SMic()
{
    const i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = MIC_SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
        .channel_format = MIC_I2S_CHANNEL_FORMAT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 256,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0,
        .mclk_multiple = I2S_MCLK_MULTIPLE_256,
        .bits_per_chan = I2S_BITS_PER_CHAN_32BIT
    };

    const i2s_pin_config_t pin_config = {
        .mck_io_num = I2S_PIN_NO_CHANGE,
        .bck_io_num = MIC_I2S_BCLK_PIN,
        .ws_io_num = MIC_I2S_WS_PIN,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = MIC_I2S_DATA_PIN
    };

    esp_err_t err = i2s_driver_install(I2S_MIC_PORT, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("I2S install failed: %d\n", err);
        return false;
    }

    err = i2s_set_pin(I2S_MIC_PORT, &pin_config);
    if (err != ESP_OK) {
        Serial.printf("I2S pin config failed: %d\n", err);
        return false;
    }

    i2s_zero_dma_buffer(I2S_MIC_PORT);
    return true;
}

double readMicDbfs()
{
    size_t bytes_read = 0;
    esp_err_t err = i2s_read(I2S_MIC_PORT, samples, sizeof(samples), &bytes_read, pdMS_TO_TICKS(1000));
    if (err != ESP_OK || bytes_read == 0) {
        Serial.printf("I2S read failed: err=%d bytes=%u\n", err, (unsigned int)bytes_read);
        return -120.0;
    }

    const size_t count = bytes_read / sizeof(samples[0]);
    double square_sum = 0.0;

    for (size_t i = 0; i < count; i++) {
        const int32_t sample24 = samples[i] >> 8;
        square_sum += (double)sample24 * (double)sample24;
    }

    const double rms = sqrt(square_sum / (double)count);
    if (rms < 1.0) {
        return -120.0;
    }

    return 20.0 * log10(rms / 8388608.0);
}

void setup()
{
    Serial.begin(115200);
    delay(1500);

    Serial.println();
    Serial.println("S3-N16R8 microphone bridge");
    Serial.printf("I2S pins: BCLK=%d WS=%d DATA=%d\n", MIC_I2S_BCLK_PIN, MIC_I2S_WS_PIN, MIC_I2S_DATA_PIN);
    Serial.printf("Sample rate: %d Hz\n", MIC_SAMPLE_RATE);

    if (!installI2SMic()) {
        Serial.println("Mic setup failed. Check pins and restart.");
        while (true) {
            delay(1000);
        }
    }

    connectWifiIfConfigured();
    Serial.println("Mic setup OK. Speak near the mic and watch the level.");
}

void loop()
{
    const double dbfs = readMicDbfs();
    Serial.printf("%7.1f dBFS %s\n", dbfs, levelBar(dbfs).c_str());

    if (dbfs >= VOICE_TRIGGER_DBFS) {
        notifyTRgbListening(dbfs);
    }
}
