# LV Single Image Milestone

This example shows one custom image on the LilyGo T-RGB display. It is the Week 2 checkpoint for the AI companion bot roadmap.

## Goal

Display `examples/lv_single_image/data/bot_face.jpg` from the SD card root.

The T-RGB cannot read a macOS path like `/Users/...` while it is running. The image must be on the board's SD card.

## Image Rules

- Use the prepared file: `examples/lv_single_image/data/bot_face.jpg`.
- It was resized from the larger PNG to `480x480`.
- Keep the SD card filename exactly `bot_face.jpg`.
- Copy it to the root of the SD card, not inside a folder.

The final SD card path should be:

```text
/bot_face.jpg
```

## Run It

1. Copy `examples/lv_single_image/data/bot_face.jpg` to the SD card root.
2. Insert the SD card into the T-RGB.
3. Build and upload the `examples/lv_single_image` sketch.
4. Open Serial Monitor at `115200`.

## Expected Result

The display shows the image centered on the screen and the Serial Monitor prints:

```text
Opening image: A:/bot_face.jpg
Loaded /bot_face.jpg
```

## Common Failures

- `SD card not found`: reinsert the SD card and reset the board.
- `Missing /bot_face.jpg`: check the filename and make sure it is on the SD card root.
- Image looks cropped: resize/crop it to `480x480`.
- Image does not decode: export it as a normal JPG and try again.
