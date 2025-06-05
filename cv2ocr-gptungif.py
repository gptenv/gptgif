from PIL import Image, ImageSequence
import numpy as np
import cv2
import os

# Reload all unique frames from earlier extraction
frame_dir = "/mnt/data"
frame_files = sorted([f for f in os.listdir(frame_dir) if f.startswith("unique_frame_") and f.endswith(".png")])
frame_paths = [os.path.join(frame_dir, f) for f in frame_files]

# Prepare OCR lookup for the known hex glyphs 0-9a-f, ideally 8x8 monochrome blocks
# We'll extract unique glyphs from the frames using connected component analysis

# First: function to convert a glyph image into a hashable format
def glyph_hash(image):
    resized = cv2.resize(image, (8, 8), interpolation=cv2.INTER_NEAREST)
    _, binary = cv2.threshold(resized, 128, 255, cv2.THRESH_BINARY)
    return tuple(binary.flatten())

# Step 1: build a glyph-to-character map from the dataset heuristically
glyph_map = {}
hex_chars = "0123456789abcdef"
glyph_freq = {}

# Collect glyphs from all frames into sets of 8x8 patches
for path in frame_paths:
    frame = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    _, binary = cv2.threshold(frame, 128, 255, cv2.THRESH_BINARY)
    height, width = binary.shape
    rows = height // 8
    cols = width // 8
    for r in range(rows):
        for c in range(cols):
            glyph = binary[r*8:(r+1)*8, c*8:(c+1)*8]
            h = glyph_hash(glyph)
            if h not in glyph_freq:
                glyph_freq[h] = 1
            else:
                glyph_freq[h] += 1

# Sort by frequency to pick most consistent glyphs
sorted_glyphs = sorted(glyph_freq.items(), key=lambda x: -x[1])[:16]
template_map = {glyph[0]: char for glyph, char in zip(sorted_glyphs, hex_chars)}

# Step 2: decode each frame using the mapped templates
decoded_hex = ""
for path in frame_paths:
    frame = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    _, binary = cv2.threshold(frame, 128, 255, cv2.THRESH_BINARY)
    height, width = binary.shape
    rows = height // 8
    cols = width // 8
    for r in range(rows):
        for c in range(cols):
            glyph = binary[r*8:(r+1)*8, c*8:(c+1)*8]
            h = glyph_hash(glyph)
            if h in template_map:
                decoded_hex += template_map[h]

# Convert the full hex string to binary ascii for BLCH
decoded_blch = ''.join(f"{int(decoded_hex[i:i+2], 16):08b}" for i in range(0, len(decoded_hex), 2))

# Save decoded BLCH to file
blch_path = "/mnt/data/extracted_from_gptgif.blch"
with open(blch_path, "w") as f:
    f.write(decoded_blch)

blch_path

