from PIL import Image, ImageSequence
import numpy as np
from sklearn.cluster import KMeans

# Load GIF and extract frames
gif_path = "/mnt/data/puzzle2.solve.unpack.loaf.blch.gptgif"
gif_image = Image.open(gif_path)

# Settings
GLYPH_WIDTH = 8
GLYPH_HEIGHT = 8
cluster_map = {i: c for i, c in enumerate("0123456789abcdef")}
glyph_tiles = []

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
                break  # Stop on blank/terminator tile
            glyph_tiles.append(np.ravel(np.ascontiguousarray(glyph)))

# Cluster the glyphs to decode into hex
X = np.stack(glyph_tiles)
kmeans = KMeans(n_clusters=16, random_state=0, n_init=10)
labels = kmeans.fit_predict(X)

# Decode to hex
decoded_hex = ''.join(cluster_map[label] for label in labels)

# Save to hex file
hex_file_path = "/mnt/data/decoded_from_gptgif.hex"
with open(hex_file_path, "w") as f:
    f.write(decoded_hex)

hex_file_path

