/**
 * @file      gif_fast.cpp
 * @brief     Incremental GIF player — frame 1 synchronous, rest background.
 */

#include "gif_fast.h"

#if LV_USE_GIF

#include "src/extra/libs/gif/gifdec.h"
#include <esp32-hal-psram.h>

/* ------------------------------------------------------------------ */
/*  Internal helpers                                                   */
/* ------------------------------------------------------------------ */

static void canvas_to_rgb565(const uint8_t *canvas, uint16_t w, uint16_t h,
                             uint8_t *dst)
{
    size_t n = (size_t)w * h;
    for (size_t i = 0; i < n; i++) {
        uint16_t c = canvas[i * 3] | ((uint16_t)canvas[i * 3 + 1] << 8);
        dst[i * 2]     = (uint8_t)(c & 0xFF);
        dst[i * 2 + 1] = (uint8_t)(c >> 8);
    }
}

/* Decode and store a single frame.  Returns true on success. */
static bool decode_one_frame(gif_fast_t *player, gd_GIF *gif)
{
    size_t frame_bytes = (size_t)gif->width * gif->height * 2;
    uint8_t *raw = (uint8_t *)ps_malloc(frame_bytes);
    if (!raw) return false;  /* PSRAM full */

    canvas_to_rgb565(gif->canvas, gif->width, gif->height, raw);

    player->frames[player->count].data     = raw;
    player->frames[player->count].size     = (uint32_t)frame_bytes;
    player->frames[player->count].delay_ms = gif->gce.delay * 10;
    if (player->frames[player->count].delay_ms == 0)
        player->frames[player->count].delay_ms = 100;
    player->count++;
    return true;
}

/* ------------------------------------------------------------------ */
/*  Forward declarations                                               */
/* ------------------------------------------------------------------ */

static void play_timer_cb(lv_timer_t *t);

/* ------------------------------------------------------------------ */
/*  Background loader — decodes frames in batches for speed            */
/* ------------------------------------------------------------------ */

static void loader_timer_cb(lv_timer_t *t)
{
    gif_fast_t *player = (gif_fast_t *)(t->user_data);
    if (!player || !player->gif) {
        lv_timer_del(t);
        if (player) player->load_timer = NULL;
        return;
    }

    gd_GIF *gif = (gd_GIF *)player->gif;

    /* Decode up to 8 frames per tick — keeps HTTP responsive */
    int batch = 8;
    while (batch-- > 0) {
        int has_next = gd_get_frame(gif);
        if (has_next <= 0) {
            gd_close_gif(gif);
            player->gif = NULL;
            break;
        }
        gd_render_frame(gif, (uint8_t *)gif->canvas);
        if (!decode_one_frame(player, gif)) {
            gd_close_gif(gif);
            player->gif = NULL;
            break;
        }
    }

    if (player->gif)
        return;  /* More frames to load next tick */

    /* Loading done — start playback at frame 2 immediately */
    lv_timer_del(t);
    player->load_timer = NULL;

    player->play_timer = lv_timer_create(play_timer_cb, 1, player);  /* fire now */
}

/* ------------------------------------------------------------------ */
/*  Playback timer — advance to next frame                             */
/* ------------------------------------------------------------------ */

static void play_timer_cb(lv_timer_t *t)
{
    gif_fast_t *player = (gif_fast_t *)(t->user_data);
    if (!player || player->count == 0) return;

    player->current++;
    if (player->current >= player->count)
        player->current = 0;

    gif_fast_frame_t *frame = &player->frames[player->current];

    player->img_dsc.data      = frame->data;
    player->img_dsc.data_size = frame->size;

    lv_timer_set_period(t, frame->delay_ms);

    if (player->img) {
        lv_img_set_src(player->img, &player->img_dsc);
    }
}

/* ------------------------------------------------------------------ */
/*  Public API                                                         */
/* ------------------------------------------------------------------ */

bool gif_fast_load(gif_fast_t *player, const char *lvgl_path)
{
    if (!player || !lvgl_path) return false;
    memset(player, 0, sizeof(*player));

    gd_GIF *gif = gd_open_gif_file(lvgl_path);
    if (!gif) return false;

    /* Allocate frame metadata (max 256 frames) */
    player->frames = (gif_fast_frame_t *)ps_malloc(256 * sizeof(gif_fast_frame_t));
    if (!player->frames) { gd_close_gif(gif); return false; }
    memset(player->frames, 0, 256 * sizeof(gif_fast_frame_t));

    player->width  = gif->width;
    player->height = gif->height;

    /* Decode frame 1 synchronously (~15ms) — near-instant transition */
    int has_first = gd_get_frame(gif);
    if (has_first <= 0) {
        free(player->frames); gd_close_gif(gif); return false;
    }
    gd_render_frame(gif, (uint8_t *)gif->canvas);
    if (!decode_one_frame(player, gif)) {
        free(player->frames); gd_close_gif(gif); return false;
    }

    /* Set up image descriptor with frame 0 */
    player->img_dsc.header.always_zero = 0;
    player->img_dsc.header.w           = player->width;
    player->img_dsc.header.h           = player->height;
    player->img_dsc.header.cf          = LV_IMG_CF_TRUE_COLOR;
    player->img_dsc.data               = player->frames[0].data;
    player->img_dsc.data_size          = player->frames[0].size;

    /* Keep GIF open — remaining frames decoded in background */
    player->gif       = gif;
    player->owns_data = true;

    return true;
}

void gif_fast_play(gif_fast_t *player, lv_obj_t *img)
{
    if (!player || player->count == 0) return;

    if (player->play_timer) { lv_timer_del(player->play_timer); player->play_timer = NULL; }
    if (player->load_timer) { lv_timer_del(player->load_timer); player->load_timer = NULL; }

    player->img     = img;
    player->current = 0;

    /* Show first frame immediately (identical to main.png for companion GIFs) */
    player->img_dsc.data      = player->frames[0].data;
    player->img_dsc.data_size = player->frames[0].size;
    lv_img_set_src(img, &player->img_dsc);
    lv_obj_center(img);
    lv_obj_clear_flag(img, LV_OBJ_FLAG_HIDDEN);

    if (player->gif) {
        /* More frames to decode — start background loader.
         * Playback auto-starts when loader finishes. */
        player->load_timer = lv_timer_create(loader_timer_cb, 1, player);
    } else {
        /* All frames already decoded */
        uint32_t delay = player->frames[0].delay_ms;
        if (delay < 10) delay = 10;
        player->play_timer = lv_timer_create(play_timer_cb, delay, player);
    }
}

void gif_fast_pause(gif_fast_t *player)
{
    if (!player) return;
    if (player->play_timer) lv_timer_pause(player->play_timer);
    if (player->load_timer) lv_timer_pause(player->load_timer);
}

bool gif_fast_is_playing(gif_fast_t *player)
{
    return player && player->play_timer != NULL;
}

void gif_fast_resume(gif_fast_t *player)
{
    if (!player) return;
    if (player->play_timer) lv_timer_resume(player->play_timer);
    if (player->load_timer) lv_timer_resume(player->load_timer);
}

void gif_fast_free(gif_fast_t *player)
{
    if (!player) return;

    if (player->play_timer) { lv_timer_del(player->play_timer); player->play_timer = NULL; }
    if (player->load_timer) { lv_timer_del(player->load_timer); player->load_timer = NULL; }

    if (player->gif) {
        gd_close_gif((gd_GIF *)player->gif);
        player->gif = NULL;
    }

    if (player->owns_data && player->frames) {
        for (uint16_t i = 0; i < player->count; i++)
            free(player->frames[i].data);
        free(player->frames);
    }

    memset(player, 0, sizeof(*player));
}

#endif /* LV_USE_GIF */
