/**
 * @file      main.cpp
 * @brief     Companion face, personality loop, memory logging, and asset upload.
 *
 * Copy examples/lv_images/data to the SD card root so the board has:
 * /data/main.jpg, /data/thumb_up.jpg, ...
 */

#include <Arduino.h>
#include <LilyGo_RGBPanel.h>
#include <LV_Helper.h>
#include <WebServer.h>
#include <WiFi.h>
#include <ctype.h>

#if __has_include("wifi_config.h")
#include "wifi_config.h"
#else
#define WIFI_SSID ""
#define WIFI_PASSWORD ""
#endif

#if !LV_USE_SJPG
#error "LVGL JPG/SJPG decoder is not enabled. Use the repo's LVGL 8 config."
#endif

#define AMBIENT_TICK_MS 800
#define MICRO_ANIMATION_MS 260
#define REMOTE_MESSAGE_HOLD_MS 15000
#define WIFI_CONNECT_TIMEOUT_MS 15000
#define SD_MEMORY_DIR "/memory"
#define SD_UPLOAD_DEFAULT_DIR "/data"
#define SD_WRITE_TEST_PATH "/memory/sd_write_test.txt"
#define SD_MOMENTS_PATH "/memory/moments.jsonl"

struct FaceState {
    const char *name;
    const char *image_path;
    const char *caption;
    uint32_t ambient_hold_ms;
};

const FaceState face_states[] = {
    {"IDLE", "/data/main.png", "Still here.", 7000},
    {"LISTENING", "/data/innocent.png", "Listening.", 5000},
    {"THINKING", "/data/confused.png", "Thinking...", 5500},
    {"SPEAKING", "/data/surprised.png", "Mm.", 5000},
    {"TEASING", "/data/wink.png", "Side-eye.", 4200},
    {"ANNOYED", "/data/angry.png", "Tiny protest.", 4200},
    {"PROUD", "/data/pround.png", "Not bad.", 5200},
    {"SLEEPY", "/data/sad.png", "Sleepy mode.", 6500},
    {"MEMORY", "/data/memory.png", "Sorting memory...", 6500},
    {"UNCERTAIN", "/data/uncertain.png", "Not sure yet.", 5200},

    // Legacy states from the earlier image-demo milestone.
    {"HAPPY", "/data/surprised.png", "That worked!", 5000},
    {"DISTRACTED", "/data/confused.png", "One sec...", 5000},
    {"MAD", "/data/angry.png", "Not amused.", 5000},
    {"TIRED", "/data/sad.png", "Low energy...", 6000},
    {"HUNGARY", "/data/main.png", "Special outfit.", 5000},
};

const size_t face_state_count = sizeof(face_states) / sizeof(face_states[0]);
const size_t ambient_sequence[] = {0, 7, 0, 4, 0, 6, 0, 2, 0, 9};
const size_t ambient_sequence_count = sizeof(ambient_sequence) / sizeof(ambient_sequence[0]);

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
static size_t ambient_cursor = 1;
static unsigned long last_remote_message_ms = 0;
static unsigned long last_state_change_ms = 0;
static uint8_t micro_phase = 0;
static File asset_upload_file;
static String asset_upload_path = "";
static String asset_upload_error = "";
static size_t asset_upload_bytes = 0;
static bool asset_upload_ok = false;

// Forward declarations
bool showFaceState(size_t index);
void showTextBubble(const char *state_name, const char *message);
int findFaceStateIndex(const String &state_name);
bool ensureMemoryDir();
bool appendSdWriteTest(const char *source, size_t *file_size);
bool appendMomentLog(const String &line, size_t *file_size);
String jsonEscape(const String &value);
String getStateList();
String sanitizeAssetFolder(const String &folder);
String sanitizeAssetFilename(const String &filename);
bool ensureSdDir(const String &dir);
bool isAllowedAssetFilename(const String &filename);
bool isDisplayableAssetFilename(const String &filename);
String sanitizeAssetPath(const String &path, const String &default_folder);
bool showAssetPath(const String &path, const char *state_name, const char *message);

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
    lv_obj_align(bubble, LV_ALIGN_BOTTOM_MID, 0, -24);
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
    return ensureSdDir(SD_MEMORY_DIR);
}

bool ensureSdDir(const String &dir)
{
    if (dir.length() == 0 || dir.charAt(0) != '/') {
        return false;
    }

    String current = "";
    int start = 1;
    while (start <= dir.length()) {
        int slash = dir.indexOf('/', start);
        String part = slash < 0 ? dir.substring(start) : dir.substring(start, slash);
        if (part.length() > 0) {
            current += "/";
            current += part;
            if (!SD_MMC.exists(current.c_str())) {
                Serial.printf("Creating directory: %s\n", current.c_str());
                if (!SD_MMC.mkdir(current.c_str())) {
                    return false;
                }
            }
        }
        if (slash < 0) {
            break;
        }
        start = slash + 1;
    }

    return true;
}

String sanitizeAssetFolder(const String &folder)
{
    String clean = folder;
    clean.trim();

    if (clean.length() == 0) {
        clean = SD_UPLOAD_DEFAULT_DIR;
    }
    if (!clean.startsWith("/")) {
        clean = "/" + clean;
    }
    while (clean.endsWith("/") && clean.length() > 1) {
        clean.remove(clean.length() - 1);
    }

    if (clean == "/" || clean.indexOf("..") >= 0 || clean.indexOf('\\') >= 0) {
        return "";
    }

    for (size_t i = 0; i < clean.length(); i++) {
        char c = clean.charAt(i);
        bool allowed = isalnum((unsigned char)c) || c == '/' || c == '_' || c == '-' || c == '.';
        if (!allowed) {
            return "";
        }
    }

    return clean;
}

String sanitizeAssetFilename(const String &filename)
{
    String clean = filename;
    clean.trim();
    clean.replace("\\", "/");

    int slash = clean.lastIndexOf('/');
    if (slash >= 0) {
        clean = clean.substring(slash + 1);
    }

    if (clean.length() == 0 || clean.startsWith(".") || clean.indexOf("..") >= 0) {
        return "";
    }

    return clean;
}

bool isAllowedAssetFilename(const String &filename)
{
    String lower = filename;
    lower.toLowerCase();
    return lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".png") || lower.endsWith(".gif") || lower.endsWith(".mp4");
}

bool isDisplayableAssetFilename(const String &filename)
{
    String lower = filename;
    lower.toLowerCase();
    return lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".png") || lower.endsWith(".gif");
}

String sanitizeAssetPath(const String &path, const String &default_folder)
{
    String clean = path;
    clean.trim();
    clean.replace("\\", "/");

    if (clean.length() == 0 || clean.indexOf("..") >= 0) {
        return "";
    }

    if (!clean.startsWith("/")) {
        String folder = sanitizeAssetFolder(default_folder);
        String filename = sanitizeAssetFilename(clean);
        if (folder.length() == 0 || filename.length() == 0) {
            return "";
        }
        return folder + "/" + filename;
    }

    int slash = clean.lastIndexOf('/');
    if (slash <= 0) {
        return "";
    }

    String folder = sanitizeAssetFolder(clean.substring(0, slash));
    String filename = sanitizeAssetFilename(clean.substring(slash + 1));
    if (folder.length() == 0 || filename.length() == 0) {
        return "";
    }

    return folder + "/" + filename;
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
    last_state_change_ms = millis();
    return true;
}

bool showAssetPath(const String &path, const char *state_name, const char *message)
{
    if (!SD_MMC.exists(path.c_str())) {
        Serial.print("Missing preview asset: ");
        Serial.println(path);
        showStatus("Missing preview asset.\nCheck /assets output.");
        return false;
    }

    String lvgl_path = lvgl_helper_get_fs_filename(path.c_str());
    Serial.print("Previewing asset: ");
    Serial.println(lvgl_path);

    lv_img_set_src(image_view, lvgl_path.c_str());
    lv_obj_center(image_view);
    showTextBubble(state_name, message);
    last_state_change_ms = millis();
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

String getStateList()
{
    String states = "";
    for (size_t i = 0; i < face_state_count; i++) {
        if (i > 0) {
            states += ", ";
        }
        states += face_states[i].name;
    }
    return states;
}

void nextAmbientState(lv_timer_t *)
{
    if (last_remote_message_ms != 0 && millis() - last_remote_message_ms < REMOTE_MESSAGE_HOLD_MS) {
        return;
    }

    if (millis() - last_state_change_ms < face_states[current_state].ambient_hold_ms) {
        return;
    }

    current_state = ambient_sequence[ambient_cursor];
    ambient_cursor++;
    ambient_cursor %= ambient_sequence_count;
    showFaceState(current_state);
}

void updateMicroAnimation(lv_timer_t *)
{
    static const int8_t bubble_offsets[] = {0, -1, -2, -1, 0, 1};
    static const uint8_t badge_opacity[] = {70, 72, 76, 72, 70, 68};
    const size_t frame_count = sizeof(bubble_offsets) / sizeof(bubble_offsets[0]);
    const size_t frame = micro_phase % frame_count;

    if (bubble) {
        lv_obj_align(bubble, LV_ALIGN_BOTTOM_MID, 0, -24 + bubble_offsets[frame]);
    }
    if (state_badge) {
        lv_obj_set_style_bg_opa(state_badge, badge_opacity[frame], 0);
    }

    micro_phase++;
}

void handleRoot()
{
    String ip = WiFi.localIP().toString();
    String body =
        "LilyGo T-RGB bot face is online.\n\n"
        "Try:\n"
        "  http://" + ip + "/say?text=Hello%20from%20my%20laptop\n"
        "  http://" + ip + "/say?state=TEASING&text=Tiny%20side-eye%20mode\n"
        "  http://" + ip + "/sd-write-test\n\n"
        "  http://" + ip + "/log?event=reply&state=HAPPY&screen_text=Hi\n\n"
        "  http://" + ip + "/personality\n\n"
        "  http://" + ip + "/assets?folder=/data\n\n"
        "  http://" + ip + "/preview?file=memory.png&text=Memory%20test\n\n"
        "States: " + getStateList() + "\n";

    server.send(200, "text/plain", body);
}

void handlePersonality()
{
    String body = "{";
    body += "\"identity\":\"memory_seed_roommate\",";
    body += "\"language\":\"Chinese-first speech, ASCII screen captions\",";
    body += "\"interaction\":\"short presence lines, soft boundaries, no lore dumps\",";
    body += "\"ambient_sequence\":[";
    for (size_t i = 0; i < ambient_sequence_count; i++) {
        if (i > 0) {
            body += ",";
        }
        body += "\"";
        body += face_states[ambient_sequence[i]].name;
        body += "\"";
    }
    body += "],\"states\":[";
    for (size_t i = 0; i < face_state_count; i++) {
        if (i > 0) {
            body += ",";
        }
        body += "{\"name\":\"";
        body += face_states[i].name;
        body += "\",\"caption\":\"";
        body += jsonEscape(face_states[i].caption);
        body += "\",\"asset\":\"";
        body += face_states[i].image_path;
        body += "\"}";
    }
    body += "]}";

    server.send(200, "application/json", body);
}

void handleListAssets()
{
    String folder = sanitizeAssetFolder(server.arg("folder"));
    if (folder.length() == 0) {
        server.send(400, "application/json", "{\"ok\":false,\"error\":\"invalid folder\"}");
        return;
    }

    File root = SD_MMC.open(folder.c_str());
    if (!root || !root.isDirectory()) {
        server.send(404, "application/json", "{\"ok\":false,\"error\":\"folder not found\"}");
        return;
    }

    String body = "{\"ok\":true,\"folder\":\"";
    body += jsonEscape(folder);
    body += "\",\"files\":[";

    bool first = true;
    File file = root.openNextFile();
    while (file) {
        if (!file.isDirectory()) {
            if (!first) {
                body += ",";
            }
            body += "{\"name\":\"";
            body += jsonEscape(String(file.name()));
            body += "\",\"size\":";
            body += String((unsigned int)file.size());
            body += "}";
            first = false;
        }
        file = root.openNextFile();
    }
    body += "]}";

    server.send(200, "application/json", body);
}

void handlePreviewAsset()
{
    String file = server.arg("file");
    if (file.length() == 0) {
        file = server.arg("path");
    }

    String folder = server.arg("folder");
    if (folder.length() == 0) {
        folder = SD_UPLOAD_DEFAULT_DIR;
    }

    String path = sanitizeAssetPath(file, folder);
    if (path.length() == 0) {
        server.send(400, "application/json", "{\"ok\":false,\"error\":\"invalid file\"}");
        return;
    }

    if (!isDisplayableAssetFilename(path)) {
        server.send(400, "application/json", "{\"ok\":false,\"error\":\"preview supports jpg, png, and gif only\"}");
        return;
    }

    String state_name = server.arg("state");
    if (state_name.length() == 0) {
        state_name = "PREVIEW";
    }

    String text = server.arg("text");
    if (text.length() == 0) {
        text = path;
    }

    bool ok = showAssetPath(path, state_name.c_str(), text.c_str());
    last_remote_message_ms = millis();

    String body = "{";
    body += "\"ok\":";
    body += ok ? "true" : "false";
    body += ",\"path\":\"";
    body += jsonEscape(path);
    body += "\"}";

    server.send(ok ? 200 : 404, "application/json", body);
}

void handleAssetUploadComplete()
{
    String body = "{";
    body += "\"ok\":";
    body += asset_upload_ok ? "true" : "false";
    body += ",\"path\":\"";
    body += jsonEscape(asset_upload_path);
    body += "\",\"size\":";
    body += String((unsigned int)asset_upload_bytes);
    if (asset_upload_error.length() > 0) {
        body += ",\"error\":\"";
        body += jsonEscape(asset_upload_error);
        body += "\"";
    }
    body += "}";

    if (asset_upload_ok) {
        showTextBubble("ASSET", "Asset upload OK.");
    } else {
        showTextBubble("ASSET", "Asset upload failed.");
    }
    last_remote_message_ms = millis();
    server.send(asset_upload_ok ? 200 : 400, "application/json", body);
}

void handleAssetUpload()
{
    HTTPUpload &upload = server.upload();

    if (upload.status == UPLOAD_FILE_START) {
        asset_upload_ok = false;
        asset_upload_error = "";
        asset_upload_path = "";
        asset_upload_bytes = 0;

        String folder = sanitizeAssetFolder(server.arg("folder"));
        String filename = sanitizeAssetFilename(upload.filename);

        if (folder.length() == 0) {
            asset_upload_error = "invalid folder";
            return;
        }
        if (filename.length() == 0) {
            asset_upload_error = "invalid filename";
            return;
        }
        if (!isAllowedAssetFilename(filename)) {
            asset_upload_error = "unsupported extension";
            return;
        }
        if (!ensureSdDir(folder)) {
            asset_upload_error = "could not create folder";
            return;
        }

        asset_upload_path = folder + "/" + filename;
        asset_upload_file = SD_MMC.open(asset_upload_path.c_str(), FILE_WRITE);
        if (!asset_upload_file) {
            asset_upload_error = "could not open target file";
            return;
        }

        Serial.printf("Asset upload start: %s\n", asset_upload_path.c_str());
    } else if (upload.status == UPLOAD_FILE_WRITE) {
        if (!asset_upload_file) {
            return;
        }

        size_t written = asset_upload_file.write(upload.buf, upload.currentSize);
        asset_upload_bytes += written;
        if (written != upload.currentSize && asset_upload_error.length() == 0) {
            asset_upload_error = "short write";
        }
    } else if (upload.status == UPLOAD_FILE_END) {
        if (asset_upload_file) {
            asset_upload_file.close();
        }
        asset_upload_ok = asset_upload_error.length() == 0 && asset_upload_path.length() > 0;
        Serial.printf("Asset upload end: %s size=%u ok=%s\n", asset_upload_path.c_str(), (unsigned int)asset_upload_bytes, asset_upload_ok ? "true" : "false");
    } else if (upload.status == UPLOAD_FILE_ABORTED) {
        if (asset_upload_file) {
            asset_upload_file.close();
        }
        asset_upload_error = "upload aborted";
        asset_upload_ok = false;
    }
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
        state_name = "SPEAKING";
    }

    int state_index = findFaceStateIndex(state_name);
    if (state_index < 0) {
        server.send(400, "text/plain", String("Unknown state. Try one of: ") + getStateList());
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
    server.on("/personality", HTTP_GET, handlePersonality);
    server.on("/assets", HTTP_GET, handleListAssets);
    server.on("/preview", HTTP_GET, handlePreviewAsset);
    server.on("/upload", HTTP_POST, handleAssetUploadComplete, handleAssetUpload);
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

    lv_timer_create(nextAmbientState, AMBIENT_TICK_MS, NULL);
    lv_timer_create(updateMicroAnimation, MICRO_ANIMATION_MS, NULL);
    connectWifi();
}

void loop()
{
    server.handleClient();
    lv_timer_handler();
    delay(2);
}
