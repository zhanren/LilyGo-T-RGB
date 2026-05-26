/**
 * @file      gif_fast.h
 * @brief     Pre-decoded GIF player — decodes all frames into PSRAM at load time,
 *            then plays back by pointer-swapping (zero LZW decode during playback).
 *
 * Usage:
 *   gif_fast_t player;
 *   gif_fast_load(&player, "/gif_loops/speak_loop.gif");
 *   gif_fast_play(&player, img_obj);   // starts playback on an lv_img
 *   gif_fast_stop(&player);            // stops and frees
 */

#pragma once

#include <lvgl.h>
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint8_t  *data;           /* raw RGB565 pixel data for this frame */
    uint32_t  size;           /* bytes (width * height * 2) */
    uint16_t  delay_ms;       /* frame delay in milliseconds */
} gif_fast_frame_t;

typedef struct {
    gif_fast_frame_t *frames; /* array of pre-decoded frames */
    uint16_t          count;  /* number of frames */
    uint16_t          width;
    uint16_t          height;
    uint16_t          current;
    lv_timer_t       *timer;
    lv_obj_t         *img;    /* target lv_img widget */
    lv_img_dsc_t      img_dsc;/* image descriptor for current frame */
    bool              owns_data;
} gif_fast_t;

/**
 * Load and pre-decode a GIF file from the given LVGL filesystem path
 * (e.g. "A:/gif_loops/speak_loop.gif").  All frames are decoded into
 * PSRAM as raw RGB565.
 *
 * Returns true on success.  Call gif_fast_free() when done.
 */
bool gif_fast_load(gif_fast_t *player, const char *lvgl_path);

/**
 * Start/resume playback on an lv_img widget.
 * The widget's source will be updated each frame.
 */
void gif_fast_play(gif_fast_t *player, lv_obj_t *img);

/** Pause playback (timer keeps running but source isn't updated). */
void gif_fast_pause(gif_fast_t *player);

/** Resume after pause. */
void gif_fast_resume(gif_fast_t *player);

/** Stop playback and free all memory. */
void gif_fast_free(gif_fast_t *player);

#ifdef __cplusplus
}
#endif
