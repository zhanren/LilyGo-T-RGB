/**
 * @file      lv_single_image.ino
 * @brief     Week 2 milestone: show one custom JPG from the SD card.
 *
 * Copy examples/lv_single_image/data/bot_face.jpg to the SD card root before
 * running. The board cannot read files from your computer after upload.
 */

#include <LilyGo_RGBPanel.h>
#include <LV_Helper.h>

#if !LV_USE_SJPG
#error "LVGL JPG/SJPG decoder is not enabled. Use the repo's LVGL 8 config."
#endif

#define IMAGE_FILENAME "/bot_face.jpg"

LilyGo_RGBPanel panel;

static lv_obj_t *status_label = NULL;

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

    if (!SD_MMC.exists(IMAGE_FILENAME)) {
        showStatus("Missing /bot_face.jpg\nCopy examples/lv_single_image/data/bot_face.jpg to the SD card root.");
        return;
    }

    String lvgl_path = lvgl_helper_get_fs_filename(IMAGE_FILENAME);
    Serial.print("Opening image: ");
    Serial.println(lvgl_path);

    lv_obj_t *img = lv_img_create(lv_scr_act());
    lv_img_set_src(img, lvgl_path.c_str());
    lv_obj_center(img);

    showStatus("Loaded /bot_face.jpg");
    lv_obj_align(status_label, LV_ALIGN_BOTTOM_MID, 0, -28);
}

void loop()
{
    lv_timer_handler();
    delay(2);
}
