/**
 * @file      gif_fast.h
 * @brief     Incremental GIF player — frame 1 synchronous, rest background.
 */

#ifndef GIF_FAST_H
#define GIF_FAST_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint8_t  *data;
    uint32_t  size;
    uint16_t  delay_ms;
} gif_fast_frame_t;

typedef struct {
    lv_img_dsc_t       img_dsc;
    gif_fast_frame_t  *frames;
    uint16_t           width;
    uint16_t           height;
    uint16_t           count;
    uint16_t           current;
    void              *gif;          /* gd_GIF * — opaque to callers */
    lv_obj_t          *img;
    lv_timer_t        *play_timer;
    lv_timer_t        *load_timer;
    bool               owns_data;
} gif_fast_t;

bool gif_fast_load(gif_fast_t *player, const char *lvgl_path);
void gif_fast_play(gif_fast_t *player, lv_obj_t *img);
void gif_fast_pause(gif_fast_t *player);
bool gif_fast_is_playing(gif_fast_t *player);
void gif_fast_resume(gif_fast_t *player);
void gif_fast_free(gif_fast_t *player);

#ifdef __cplusplus
}
#endif

#endif /* GIF_FAST_H */
