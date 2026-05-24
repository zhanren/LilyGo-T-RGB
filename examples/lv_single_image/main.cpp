/**
 * @file      main.cpp
 * @brief     Week 13 milestone: companion personality and memory logging.
 *
 * Copy examples/lv_images/data to the SD card root so the board has:
 * /data/main.jpg, /data/thumb_up.jpg, ...
 */

#include <Arduino.h>
#include <LilyGo_RGBPanel.h>
#include <LV_Helper.h>
#include <WebServer.h>
#include <WiFi.h>

#if __has_include("wifi_config.h")
#include "wifi_config.h"
#else
#define WIFI_SSID ""
#define WIFI_PASSWORD ""
#endif

#if !LV_USE_SJPG
#error "LVGL JPG/SJPG decoder is not enabled. Use the repo's LVGL 8 config."
#endif

#define FACE_STATE_CHANGE_MS 3000
#define REMOTE_MESSAGE_HOLD_MS 15000
#define WIFI_CONNECT_TIMEOUT_MS 15000
#define SD_MEMORY_DIR "/memory"
#define SD_WRITE_TEST_PATH "/memory/sd_write_test.txt"
#define SD_MOMENTS_PATH "/memory/moments.jsonl"

struct FaceState {
    const char *name;
    const char *image_path;
    const char *caption;
};

const FaceState face_states[] = {
    {"IDLE", "/data/main.jpg", "Waiting..."},
    {"HAPPY", "/data/thumb_up.jpg", "That worked!"},
    {"DISTRACTED", "/data/distracting.jpg", "One sec..."},
    {"MAD", "/data/mad.jpg", "Not amused."},
    {"TIRED", "/data/tired.jpg", "Low energy..."},
    {"HUNGARY", "/data/hungary.jpg", "Special outfit."},
};

const size_t face_state_count = sizeof(face_states) / sizeof(face_states[0]);

LilyGo_RGBPanel panel;
WebServer server(80);

static lv_obj_t *status_label = NULL;
static lv_obj_t *bubble = NULL;
static lv_obj_t *bubble_label = NULL;
static lv_obj_t *image_view = NULL;
static lv_obj_t *state_badge = NULL;
static lv_obj_t *state_badge_label = NULL;
static lv_obj_t *wifi_label = NULL;
static size_t current_state = 0;
static unsigned long last_remote_message_ms = 0;

// Forward declarations
bool showFaceState(size_t index);
void showTextBubble(const char *state_name, const char *message);
int findFaceStateIndex(const String &state_name);
bool ensureMemoryDir();
bool appendSdWriteTest(const char *source, size_t *file_size);
bool appendMomentLog(const String &line, size_t *file_size);
String jsonEscape(const String &value);

void createTextBubble()
{
    bubble = lv_obj_create(lv_scr_act());
    lv_obj_set_size(bubble, 392, 92);
    lv_obj_align(bubble, LV_ALIGN_BOTTOM_MID, 0, -24);
    lv_obj_set_style_radius(bubble, 18, 0);
    lv_obj_set_style_bg_color(bubble, lv_color_hex(0x111318), 0);
    lv_obj_set_style_bg_opa(bubble, LV_OPA_80, 0);
    lv_obj_set_style_border_color(bubble, lv_color_white(), 0);
    lv_obj_set_style_border_opa(bubble, LV_OPA_40, 0);
    lv_obj_set_style_border_width(bubble, 2, 0);
    lv_obj_set_style_pad_all(bubble, 12, 0);

    bubble_label = lv_label_create(bubble);
    lv_obj_set_width(bubble_label, 360);
    lv_label_set_long_mode(bubble_label, LV_LABEL_LONG_WRAP);
    lv_obj_set_style_text_align(bubble_label, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_set_style_text_color(bubble_label, lv_color_white(), 0);
    lv_obj_center(bubble_label);
}

void createStateBadge()
{
    state_badge = lv_obj_create(lv_scr_act());
    lv_obj_set_size(state_badge, 180, 42);
    lv_obj_align(state_badge, LV_ALIGN_TOP_MID, 0, 34);
    lv_obj_set_style_radius(state_badge, 18, 0);
    lv_obj_set_style_bg_color(state_badge, lv_color_hex(0x111318), 0);
    lv_obj_set_style_bg_opa(state_badge, LV_OPA_70, 0);
    lv_obj_set_style_border_width(state_badge, 0, 0);
    lv_obj_set_style_pad_all(state_badge, 6, 0);

    state_badge_label = lv_label_create(state_badge);
    lv_obj_set_style_text_align(state_badge_label, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_set_style_text_color(state_badge_label, lv_color_white(), 0);
    lv_obj_center(state_badge_label);
}

void createWifiLabel()
{
    wifi_label = lv_label_create(lv_scr_act());
    lv_obj_set_width(wifi_label, 360);
    lv_label_set_long_mode(wifi_label, LV_LABEL_LONG_DOT);
    lv_obj_set_style_text_align(wifi_label, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_set_style_text_color(wifi_label, lv_color_white(), 0);
    lv_obj_align(wifi_label, LV_ALIGN_TOP_MID, 0, 82);
    lv_label_set_text(wifi_label, "Wi-Fi: not started");
}

void showTextBubble(const char *state_name, const char *message)
{
    lv_label_set_text(state_badge_label, state_name);
    lv_label_set_text(bubble_label, message);
    Serial.print(state_name);
    Serial.print(": ");
    Serial.println(message);
}

void setWifiStatus(const String &message)
{
    lv_label_set_text(wifi_label, message.c_str());
    Serial.println(message);
    lv_timer_handler();
}

void showStatus(const char *message)
{
    if (!status_label) {
        status_label = lv_label_create(lv_scr_act());
        lv_obj_set_width(status_label, 420);
        lv_label_set_long_mode(status_label, LV_LABEL_LONG_WRAP);
        lv_obj_set_style_text_align(status_label, LV_TEXT_ALIGN_CENTER, 0);
        lv_obj_set_style_text_color(status_label, lv_color_white(), 0);
        lv_obj_align(status_label, LV_ALIGN_CENTER, 0, 0);
    }

    lv_label_set_text(status_label, message);
    Serial.println(message);
}

void listDir(fs::FS &fs, const char *dirname)
{
    Serial.printf("Listing directory: %s\n", dirname);

    File root = fs.open(dirname);
    if (!root || !root.isDirectory()) {
        Serial.println("Failed to open directory");
        return;
    }

    File file = root.openNextFile();
    while (file) {
        Serial.printf("  FILE: %s  SIZE: %u\n", file.name(), (unsigned int)file.size());
        file = root.openNextFile();
    }
}

bool ensureMemoryDir()
{
    if (SD_MMC.exists(SD_MEMORY_DIR)) {
        return true;
    }

    Serial.printf("Creating directory: %s\n", SD_MEMORY_DIR);
    return SD_MMC.mkdir(SD_MEMORY_DIR);
}

bool appendSdWriteTest(const char *source, size_t *file_size)
{
    if (!ensureMemoryDir()) {
        Serial.println("Failed to create /memory directory");
        return false;
    }

    File file = SD_MMC.open(SD_WRITE_TEST_PATH, FILE_APPEND);
    if (!file) {
        Serial.printf("Failed to open %s for append\n", SD_WRITE_TEST_PATH);
        return false;
    }

    String line = "ms=" + String(millis());
    line += ", source=";
    line += source;
    line += ", state=";
    line += face_states[current_state].name;
    line += "\n";

    size_t written = file.print(line);
    file.close();

    if (written != line.length()) {
        Serial.printf("Short write to %s: %u of %u bytes\n", SD_WRITE_TEST_PATH, (unsigned int)written, (unsigned int)line.length());
        return false;
    }

    File readback = SD_MMC.open(SD_WRITE_TEST_PATH, FILE_READ);
    if (!readback) {
        Serial.printf("Failed to reopen %s for readback\n", SD_WRITE_TEST_PATH);
        return false;
    }

    if (file_size) {
        *file_size = readback.size();
    }
    readback.close();

    Serial.printf("SD write OK: %s size=%u\n", SD_WRITE_TEST_PATH, file_size ? (unsigned int)*file_size : 0);
    return true;
}

String jsonEscape(const String &value)
{
    String escaped = "";
    for (size_t i = 0; i < value.length(); i++) {
        char c = value.charAt(i);
        if (c == '\\' || c == '"') {
            escaped += '\\';
            escaped += c;
        } else if (c == '\n' || c == '\r' || c == '\t') {
            escaped += ' ';
        } else if ((uint8_t)c < 32) {
            escaped += ' ';
        } else {
            escaped += c;
        }
    }
    return escaped;
}

bool appendMomentLog(const String &line, size_t *file_size)
{
    if (!ensureMemoryDir()) {
        Serial.println("Failed to create /memory directory");
        return false;
    }

    File file = SD_MMC.open(SD_MOMENTS_PATH, FILE_APPEND);
    if (!file) {
        Serial.printf("Failed to open %s for append\n", SD_MOMENTS_PATH);
        return false;
    }

    size_t written = file.print(line);
    written += file.print("\n");
    file.close();

    if (written != line.length() + 1) {
        Serial.printf("Short write to %s: %u of %u bytes\n", SD_MOMENTS_PATH, (unsigned int)written, (unsigned int)(line.length() + 1));
        return false;
    }

    File readback = SD_MMC.open(SD_MOMENTS_PATH, FILE_READ);
    if (!readback) {
        Serial.printf("Failed to reopen %s for readback\n", SD_MOMENTS_PATH);
        return false;
    }

    if (file_size) {
        *file_size = readback.size();
    }
    readback.close();

    Serial.printf("Moment log OK: %s size=%u\n", SD_MOMENTS_PATH, file_size ? (unsigned int)*file_size : 0);
    return true;
}

bool showFaceState(size_t index)
{
    const FaceState &state = face_states[index];
    const char *sd_path = state.image_path;

    if (!SD_MMC.exists(sd_path)) {
        Serial.print("Missing image: ");
        Serial.println(sd_path);
        showStatus("Missing slideshow image.\nCheck Serial Monitor for filename.");
        return false;
    }

    String lvgl_path = lvgl_helper_get_fs_filename(sd_path);
    Serial.print("Opening image: ");
    Serial.println(lvgl_path);

    lv_img_set_src(image_view, lvgl_path.c_str());
    lv_obj_center(image_view);

    showTextBubble(state.name, state.caption);
    return true;
}

int findFaceStateIndex(const String &state_name)
{
    for (size_t i = 0; i < face_state_count; i++) {
        if (state_name.equalsIgnoreCase(face_states[i].name)) {
            return i;
        }
    }
    return -1;
}

void nextFaceState(lv_timer_t *)
{
    if (last_remote_message_ms != 0 && millis() - last_remote_message_ms < REMOTE_MESSAGE_HOLD_MS) {
        return;
    }

    current_state++;
    current_state %= face_state_count;
    showFaceState(current_state);
}

void handleRoot()
{
    String ip = WiFi.localIP().toString();
    String body =
        "LilyGo T-RGB bot face is online.\n\n"
        "Try:\n"
        "  http://" + ip + "/say?text=Hello%20from%20my%20laptop\n"
        "  http://" + ip + "/say?state=HAPPY&text=That%20worked\n"
        "  http://" + ip + "/sd-write-test\n\n"
        "  http://" + ip + "/log?event=reply&state=HAPPY&screen_text=Hi\n\n"
        "States: IDLE, HAPPY, DISTRACTED, MAD, TIRED, HUNGARY\n";

    server.send(200, "text/plain", body);
}

void handleSdWriteTest()
{
    size_t file_size = 0;
    bool ok = appendSdWriteTest("http", &file_size);

    if (ok) {
        showTextBubble("MEMORY", "SD write OK.");
    } else {
        showTextBubble("MEMORY", "SD write failed.");
    }
    last_remote_message_ms = millis();

    String body = "{";
    body += "\"ok\":";
    body += ok ? "true" : "false";
    body += ",\"path\":\"";
    body += SD_WRITE_TEST_PATH;
    body += "\",\"size\":";
    body += String(file_size);
    body += "}";

    server.send(ok ? 200 : 500, "application/json", body);
}

void handleLog()
{
    String event = server.arg("event");
    String source = server.arg("source");
    String state = server.arg("state");
    String screen_text = server.arg("screen_text");
    String speech_text = server.arg("speech_text");
    String memory = server.arg("memory");
    String prompt = server.arg("prompt");

    if (event.length() == 0) event = "reply";
    if (source.length() == 0) source = "laptop";
    if (state.length() == 0) state = face_states[current_state].name;

    String line = "{";
    line += "\"ms\":" + String(millis()) + ",";
    line += "\"event\":\"" + jsonEscape(event) + "\",";
    line += "\"source\":\"" + jsonEscape(source) + "\",";
    line += "\"state\":\"" + jsonEscape(state) + "\",";
    line += "\"face_state\":\"" + String(face_states[current_state].name) + "\",";
    line += "\"screen_text\":\"" + jsonEscape(screen_text) + "\",";
    line += "\"speech_text\":\"" + jsonEscape(speech_text) + "\",";
    line += "\"memory_candidate\":\"" + jsonEscape(memory) + "\",";
    line += "\"prompt\":\"" + jsonEscape(prompt) + "\"";
    line += "}";

    size_t file_size = 0;
    bool ok = appendMomentLog(line, &file_size);

    String body = "{";
    body += "\"ok\":";
    body += ok ? "true" : "false";
    body += ",\"path\":\"";
    body += SD_MOMENTS_PATH;
    body += "\",\"size\":";
    body += String(file_size);
    body += "}";

    server.send(ok ? 200 : 500, "application/json", body);
}

void handleSay()
{
    String text = server.arg("text");
    String state_name = server.arg("state");

    if (text.length() == 0) {
        text = "Hello from laptop.";
    }

    if (state_name.length() == 0) {
        state_name = "HAPPY";
    }

    int state_index = findFaceStateIndex(state_name);
    if (state_index < 0) {
        server.send(400, "text/plain", "Unknown state. Try IDLE, HAPPY, DISTRACTED, MAD, TIRED, or HUNGARY.");
        return;
    }

    current_state = (size_t)state_index;
    if (!showFaceState(current_state)) {
        server.send(500, "text/plain", "State image is missing on the SD card.");
        return;
    }

    showTextBubble(face_states[current_state].name, text.c_str());
    last_remote_message_ms = millis();
    server.send(200, "text/plain", "OK");
}

void startHttpServer()
{
    server.on("/", HTTP_GET, handleRoot);
    server.on("/say", HTTP_GET, handleSay);
    server.on("/sd-write-test", HTTP_GET, handleSdWriteTest);
    server.on("/log", HTTP_GET, handleLog);
    server.begin();

    String ip = WiFi.localIP().toString();
    Serial.print("HTTP server: http://");
    Serial.println(ip);
}

void connectWifi()
{
    if (strlen(WIFI_SSID) == 0) {
        setWifiStatus("Wi-Fi: add wifi_config.h");
        showTextBubble("SETUP", "Copy wifi_config.example.h to wifi_config.h.");
        return;
    }

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    setWifiStatus(String("Wi-Fi: connecting to ") + WIFI_SSID);

    unsigned long start_ms = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start_ms < WIFI_CONNECT_TIMEOUT_MS) {
        delay(250);
        Serial.print(".");
        lv_timer_handler();
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        String ip = WiFi.localIP().toString();
        setWifiStatus(String("Wi-Fi: ") + ip);
        showTextBubble("ONLINE", String("Connected at " + ip).c_str());
        startHttpServer();
        return;
    }

    setWifiStatus("Wi-Fi: connection failed");
    showTextBubble("OFFLINE", "Check SSID/password and reset.");
}

void setup()
{
    Serial.begin(115200);
    delay(1000);

    bool panel_ready = panel.begin();
    if (!panel_ready) {
        while (true) {
            Serial.println("Error: failed to initialize T-RGB");
            delay(1000);
        }
    }

    beginLvglHelper(panel);
    panel.setBrightness(16);
    lv_obj_set_style_bg_color(lv_scr_act(), lv_color_hex(0x111318), 0);

    if (!panel.installSD()) {
        showStatus("SD card not found.\nInsert the SD card, then reset.");
        return;
    }

    listDir(SD_MMC, "/");
    listDir(SD_MMC, "/data");
    ensureMemoryDir();
    listDir(SD_MMC, "/memory");

    image_view = lv_img_create(lv_scr_act());
    lv_obj_center(image_view);
    createStateBadge();
    createWifiLabel();
    createTextBubble();

    if (!showFaceState(current_state)) {
        return;
    }

    lv_timer_create(nextFaceState, FACE_STATE_CHANGE_MS, NULL);
    connectWifi();
}

void loop()
{
    server.handleClient();
    lv_timer_handler();
    delay(2);
}
