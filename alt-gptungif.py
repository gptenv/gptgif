# Re-import necessary modules after code execution environment reset
from PIL import Image, ImageSequence
import numpy as np
from sklearn.cluster import KMeans
import os

# Re-define constants and paths
GLYPH_WIDTH = 8
GLYPH_HEIGHT = 8
gif_path = "/mnt/data/puzzle2.solve.unpack.loaf.blch.gptgif"
hex_file_path = "/mnt/data/decoded_from_gptgif.hex"
cluster_map = {i: c for i, c in enumerate("0123456789abcdef")}
glyph_tiles = []

# Load GIF and extract frames
gif_image = Image.open(gif_path)

# Extract glyph tiles from each frame
for frame in ImageSequence.Iterator(gif_image):
    grayscale = frame.convert("L")
    binary = (np.array(grayscale) > 128).astype(np.uint8)
    height, width = binary.shape
    rows = height // GLYPH_HEIGHT
    cols = width // GLYPH_WIDTH

    for row in range(rows):
        for col in range(cols):
            y0 = row * GLYPH_HEIGHT
            x0 = col * GLYPH_WIDTH
            glyph = binary[y0:y0+GLYPH_HEIGHT, x0:x0+GLYPH_WIDTH]
            if np.sum(glyph) < 5:
                break
            glyph_tiles.append(np.ravel(np.ascontiguousarray(glyph)))

# Perform clustering and decode to hex string
X = np.stack(glyph_tiles)
kmeans = KMeans(n_clusters=16, random_state=0, n_init=10)
labels = kmeans.fit_predict(X)
decoded_hex = ''.join(cluster_map[label] for label in labels)

# Save to hex file
with open(hex_file_path, "w") as f:
    f.write(decoded_hex)

hex_file_path

