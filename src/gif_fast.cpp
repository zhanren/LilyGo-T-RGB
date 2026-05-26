/**
 * @file      gif_fast.cpp
 * @brief     Pre-decoded GIF player implementation.
 */

#include "gif_fast.h"

#if LV_USE_GIF

#include "src/extra/libs/gif/gifdec.h"
#include <esp32-hal-psram.h>

/* ------------------------------------------------------------------ */
/*  Internal helpers                                                   */
/* ------------------------------------------------------------------ */

/* Convert gd_GIF canvas (TRUE_COLOR_ALPHA, 3 Bpp) → raw RGB565.
 * canvas layout (LV_COLOR_DEPTH==16):  [R5G6B5_lo, R5G6B5_hi, alpha]
 * We strip the alpha byte. */
static void canvas_to_rgb565(const uint8_t *canvas, uint16_t w, uint16_t h,
                             uint8_t *dst)
{
    size_t pixel_count = (size_t)w * h;
    for (size_t i = 0; i < pixel_count; i++) {
        /* canvas[i*3] = low byte of RGB565, canvas[i*3+1] = high byte */
        uint16_t c = canvas[i * 3] | ((uint16_t)canvas[i * 3 + 1] << 8);
        dst[i * 2]     = (uint8_t)(c & 0xFF);
        dst[i * 2 + 1] = (uint8_t)(c >> 8);
    }
}

/* Decode ALL frames from an already-opened gd_GIF, storing raw RGB565 in PSRAM.
 * Returns number of frames decoded, or 0 on error. */
static uint16_t decode_all_frames(gd_GIF *gif,
                                  gif_fast_frame_t **out_frames,
                                  uint16_t *out_width,
                                  uint16_t *out_height)
{
    /* First, count frames and collect delays */
    uint16_t max_frames = 256;  /* reasonable upper bound; we'll grow if needed */
    gif_fast_frame_t *frames =
        (gif_fast_frame_t *)ps_malloc(max_frames * sizeof(gif_fast_frame_t));
    if (!frames) return 0;

    uint16_t count = 0;

    /* Decode loop — we do a full pass */
    for (;;) {
        int has_next = gd_get_frame(gif);
        if (has_next <= 0) break;  /* 0 = end, -1 = error */

        /* Grow array if needed */
        if (count >= max_frames) {
            max_frames *= 2;
            gif_fast_frame_t *new_frames =
                (gif_fast_frame_t *)ps_realloc(frames,
                    max_frames * sizeof(gif_fast_frame_t));
            if (!new_frames) {
                /* free what we have so far */
                for (uint16_t j = 0; j < count; j++)
                    free(frames[j].data);
                free(frames);
                return 0;
            }
            frames = new_frames;
        }

        gd_render_frame(gif, (uint8_t *)gif->canvas);

        /* Allocate raw RGB565 buffer in PSRAM */
        size_t frame_bytes = (size_t)gif->width * gif->height * 2;
        uint8_t *raw = (uint8_t *)ps_malloc(frame_bytes);
        if (!raw) break;  /* PSRAM full — use whatever frames we decoded */

        canvas_to_rgb565(gif->canvas, gif->width, gif->height, raw);

        frames[count].data     = raw;
        frames[count].size     = (uint32_t)frame_bytes;
        frames[count].delay_ms = gif->gce.delay * 10;  /* GIF delay is in 1/100 s */
        if (frames[count].delay_ms == 0)
            frames[count].delay_ms = 100;  /* default 10 fps */
        count++;
    }

    *out_frames = frames;
    *out_width  = gif->width;
    *out_height = gif->height;
    return count;
}

/* ------------------------------------------------------------------ */
/*  Timer callback — advance to next frame                             */
/* ------------------------------------------------------------------ */

static void gif_fast_timer_cb(lv_timer_t *t)
{
    gif_fast_t *player = (gif_fast_t *)(t->user_data);
    if (!player || player->count == 0) return;

    player->current++;
    if (player->current >= player->count)
        player->current = 0;

    gif_fast_frame_t *frame = &player->frames[player->current];

    /* Update image descriptor to point to this frame's raw data */
    player->img_dsc.data = frame->data;
    player->img_dsc.data_size = frame->size;

    /* Update timer period to match this frame's delay */
    lv_timer_set_period(t, frame->delay_ms);

    /* Tell LVGL to redraw the image */
    if (player->img) {
        lv_img_cache_invalidate_src(&player->img_dsc);
        lv_img_set_src(player->img, &player->img_dsc);
        lv_obj_invalidate(player->img);
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

    uint16_t count = decode_all_frames(gif, &player->frames,
                                       &player->width, &player->height);
    gd_close_gif(gif);

    if (count == 0) return false;

    player->count     = count;
    player->current   = 0;
    player->owns_data = true;

    /* Set up the reusable image descriptor */
    player->img_dsc.header.always_zero = 0;
    player->img_dsc.header.w           = player->width;
    player->img_dsc.header.h           = player->height;
    player->img_dsc.header.cf          = LV_IMG_CF_TRUE_COLOR;
    player->img_dsc.data               = player->frames[0].data;
    player->img_dsc.data_size          = player->frames[0].size;

    LV_LOG_USER("gif_fast: loaded %u frames, %ux%u",
                count, player->width, player->height);

    return true;
}

void gif_fast_play(gif_fast_t *player, lv_obj_t *img)
{
    if (!player || player->count == 0) return;

    /* Stop any existing timer */
    if (player->timer) {
        lv_timer_del(player->timer);
        player->timer = NULL;
    }

    player->img     = img;
    player->current = 0;

    /* Show first frame immediately */
    player->img_dsc.data = player->frames[0].data;
    player->img_dsc.data_size = player->frames[0].size;
    lv_img_set_src(img, &player->img_dsc);
    lv_obj_center(img);
    lv_obj_clear_flag(img, LV_OBJ_FLAG_HIDDEN);

    /* Start timer for subsequent frames */
    uint32_t delay = player->frames[0].delay_ms;
    if (delay < 10) delay = 10;
    player->timer = lv_timer_create(gif_fast_timer_cb, delay, player);
}

void gif_fast_pause(gif_fast_t *player)
{
    if (player && player->timer)
        lv_timer_pause(player->timer);
}

void gif_fast_resume(gif_fast_t *player)
{
    if (player && player->timer)
        lv_timer_resume(player->timer);
}

void gif_fast_free(gif_fast_t *player)
{
    if (!player) return;

    if (player->timer) {
        lv_timer_del(player->timer);
        player->timer = NULL;
    }

    if (player->owns_data && player->frames) {
        for (uint16_t i = 0; i < player->count; i++) {
            free(player->frames[i].data);
        }
        free(player->frames);
    }

    memset(player, 0, sizeof(*player));
}

#endif /* LV_USE_GIF */
