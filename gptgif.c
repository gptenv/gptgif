// .gptgif.gif file type encoder. Reference C implementation with animated directional gradient glyphs.
// Written by Tuesday and Jeremy Carter, modified with GPT orientation logic.
// Licensed under MIT License.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <gif_lib.h>

#define WIDTH 640
#define HEIGHT 480
#define GLYPH_WIDTH 8
#define GLYPH_HEIGHT 8
#define COLS (WIDTH / GLYPH_WIDTH)
#define ROWS (HEIGHT / GLYPH_HEIGHT)
#define FRAME_CHARS (COLS * ROWS)
#define INITIAL_HEX_CAPACITY 1024
#define COLOR_COUNT 256

const char *hex_chars = "0123456789abcdef";

// Compressed DOS-style hex font with 1px spacing margin inside each 8x8 cell
unsigned char font[16][8] = {
    {0x00,0x3C,0x66,0x6E,0x76,0x66,0x3C,0x00}, // 0
    {0x00,0x18,0x38,0x18,0x18,0x18,0x3C,0x00}, // 1
    {0x00,0x3C,0x66,0x0C,0x18,0x30,0x7E,0x00}, // 2
    {0x00,0x3C,0x66,0x1C,0x06,0x66,0x3C,0x00}, // 3
    {0x00,0x0C,0x1C,0x2C,0x4C,0x7E,0x0C,0x00}, // 4
    {0x00,0x7E,0x60,0x7C,0x06,0x66,0x3C,0x00}, // 5
    {0x00,0x3C,0x60,0x7C,0x66,0x66,0x3C,0x00}, // 6
    {0x00,0x7E,0x06,0x0C,0x18,0x30,0x30,0x00}, // 7
    {0x00,0x3C,0x66,0x3C,0x66,0x66,0x3C,0x00}, // 8
    {0x00,0x3C,0x66,0x66,0x3E,0x06,0x3C,0x00}, // 9
    {0x00,0x3C,0x06,0x3E,0x66,0x66,0x3E,0x00}, // a
    {0x00,0x60,0x60,0x7C,0x66,0x66,0x7C,0x00}, // b
    {0x00,0x3C,0x60,0x60,0x60,0x60,0x3C,0x00}, // c
    {0x00,0x06,0x06,0x3E,0x66,0x66,0x3E,0x00}, // d
    {0x00,0x3C,0x66,0x7E,0x60,0x60,0x3C,0x00}, // e
    {0x00,0x1C,0x30,0x30,0x7C,0x30,0x30,0x00}  // f
};

void draw_char(GifByteType *raster, int x, int y, char c, int frame) {
    char *match = strchr(hex_chars, c);
    if (!match) return;
    const unsigned char *glyph = font[match - hex_chars];
    for (int dy = 0; dy < GLYPH_HEIGHT; dy++) {
        for (int dx = 0; dx < GLYPH_WIDTH; dx++) {
            int idx = (y + dy) * WIDTH + (x + dx);
            if (glyph[dy] & (1 << (7 - dx))) {
                int brightness = 32 + ((frame + dy + dx) % 223);  // Avoid background index 0
                raster[idx] = brightness;
            }
        }
    }
}

void draw_frame(GifFileType *gif, const char *data, int len, int frame) {
    GifByteType *raster = calloc(WIDTH * HEIGHT, 1);
    unsigned char gce[4] = {0x00, 30, 0x00, 0x00};
    EGifPutExtension(gif, GRAPHICS_EXT_FUNC_CODE, 4, gce);
    EGifPutImageDesc(gif, 0, 0, WIDTH, HEIGHT, false, NULL);
    for (int i = 0; i < len && i < FRAME_CHARS; i++) {
        int row = i / COLS, col = i % COLS;
        draw_char(raster, col * GLYPH_WIDTH, row * GLYPH_HEIGHT, data[i], frame);
    }
    for (int y = 0; y < HEIGHT; y++) EGifPutLine(gif, &raster[y * WIDTH], WIDTH);
    free(raster);
}

int main(int argc, char *argv[]) {
    if (argc < 4 || strcmp(argv[1], "cf") != 0) {
        fprintf(stderr, "Usage: %s cf output.gptgif.gif input1 [input2 ...]\n", argv[0]);
        return 1;
    }

    size_t hex_capacity = INITIAL_HEX_CAPACITY;
    char *hex = malloc(hex_capacity);
    int hex_len = 0;

    for (int f = 3; f < argc; f++) {
        FILE *in = fopen(argv[f], "rb");
        if (!in) continue;
        int c;
        while ((c = fgetc(in)) != EOF) {
            if (hex_len + 2 >= hex_capacity) {
                hex_capacity *= 2;
                char *new_hex = realloc(hex, hex_capacity);
                if (!new_hex) {
                    fprintf(stderr, "Memory allocation failed\n");
                    free(hex);
                    return 1;
                }
                hex = new_hex;
            }
            snprintf(&hex[hex_len], 3, "%02x", c);
            hex_len += 2;
        }
        fclose(in);
    }

    int error;
    GifFileType *gif = EGifOpenFileName(argv[2], false, &error);
    ColorMapObject *cmap = GifMakeMapObject(COLOR_COUNT, NULL);

    // Set index 0 to be solid black background
    cmap->Colors[0].Red = 0;
    cmap->Colors[0].Green = 0;
    cmap->Colors[0].Blue = 0;

    // Color palette gradient from index 1–255
    for (int i = 1; i < COLOR_COUNT; i++) {
        cmap->Colors[i].Red = (i < 128) ? i * 2 : 255;
        cmap->Colors[i].Green = (i < 128) ? 255 - i * 2 : (i - 128) * 2;
        cmap->Colors[i].Blue = 255 - i;
    }

    EGifPutScreenDesc(gif, WIDTH, HEIGHT, 8, 0, cmap);

    for (int offset = 0, frame = 0; offset < hex_len; offset += FRAME_CHARS, frame++) {
        int chunk = (hex_len - offset > FRAME_CHARS) ? FRAME_CHARS : (hex_len - offset);
        draw_frame(gif, &hex[offset], chunk, frame);
    }

    EGifCloseFile(gif, &error);
    GifFreeMapObject(cmap);
    free(hex);
    return 0;
}
