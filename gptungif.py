#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# gptungif.py - gptungif is a .gptgif file format (a certain type of standard .gif file), 
# decoder tool (reference python implementation).
#
# Extracts visual hex values from an animated GIF file and decodes it using 
# the xxd -p -r command, then zips it with gzip -9 before outputting. Meant to be used in 
# conjunction with an encoder program "gptgif" that generates the GIF file, which contains 
# visual representations of hex values (0-9, a-f) in a specific font.
#
# Licensed under the MIT License. Copyright (c) 2025 Jeremy Carter <defcron@gptenv.com>, 
# Tim and Tuesday Custom GPTs, and GPT-4o (ChatGPT), Gemini 2.0 Flash Code Assist in vscode 
# (gemini.google.com).
import sys
import io
import numpy as np
from PIL import Image, ImageSequence
import subprocess
from sklearn.cluster import KMeans

GLYPH_WIDTH = 8
GLYPH_HEIGHT = 8

# --- IMPORTANT: CALIBRATION REQUIRED FOR THIS MAPPING ---
# The PRETRAINED_MAPPING below is a TEMPLATE. K-Means assigns cluster labels
# (0-15) arbitrarily. You MUST calibrate this mapping by:
#   1. Generating a GIF with your C encoder that clearly shows all 16 unique
#      hex characters (0-9, a-f).
#   2. Running this script on that GIF up to the point K-Means assigns 'labels'.
#   3. For each cluster label (0-15), visually inspect the glyphs belonging to
#      that cluster (or the cluster centroid) to determine which actual hex
#      character it represents.
#   4. Update the mapping below with these empirically determined assignments.
#
# The mapping MUST be one-to-one: 16 unique cluster labels to 16 unique
# lowercase hex characters.
#
# The previous mapping was problematic as it was not one-to-one and used
# uppercase hex characters.
PRETRAINED_MAPPING = {
    0: '0',  1: '4',  2: 'b',  3: '1',
    4: '7',  5: 'a',  6: '6',  7: '9',
    8: '2',  9: '3',  10: 'd', 11: 'e',
    12: '5', 13: 'f', 14: 'c', 15: '8'
    # Example: If K-Means cluster '0' consistently represents 'f',
    # and cluster '1' represents '3', etc., update accordingly.
}

def extract_hex_from_gif(gif_bytes, calibrate=False):
    gif_image = Image.open(io.BytesIO(gif_bytes))
    glyph_tiles = []
    extraction_halted = False

    for frame in ImageSequence.Iterator(gif_image):
        if extraction_halted:
            break
        grayscale = frame.convert("L")
        # Binarize pixels: Assuming light ink on a dark background.
        binary = (np.array(grayscale) > 128).astype(np.uint8)
        height, width = binary.shape
        rows = height // GLYPH_HEIGHT
        cols = width // GLYPH_WIDTH

        for row in range(rows):
            if extraction_halted:
                break
            for col in range(cols):
                y0 = row * GLYPH_HEIGHT
                x0 = col * GLYPH_WIDTH
                glyph = binary[y0:y0+GLYPH_HEIGHT, x0:x0+GLYPH_WIDTH]
                # Heuristic: if a glyph has very few ink pixels (e.g., < 5 out of 64),
                # assume it's padding and stop extracting.
                if np.sum(glyph) < 5: # Threshold for "empty" or "padding" glyph
                    extraction_halted = True
                    break
                glyph_tiles.append(glyph)

    flat_tiles = [np.ravel(np.ascontiguousarray(tile)) for tile in glyph_tiles]
    X = np.stack(flat_tiles)
    kmeans = KMeans(n_clusters=16, random_state=0, n_init=10) # n_init='auto' in newer sklearn
    labels = kmeans.fit_predict(X)

    # --- For Calibration: Print cluster centers ---
    if calibrate:
        print("K-Means Cluster Centroids (visualized as 8x8 glyphs):", file=sys.stderr)
        print("Inspect these to map K-Means cluster labels (0-15) to actual hex characters.", file=sys.stderr)
        for i, center_vector in enumerate(kmeans.cluster_centers_):
            print(f"\nCluster Label: {i}", file=sys.stderr)
            glyph_center = center_vector.reshape(GLYPH_HEIGHT, GLYPH_WIDTH)
            for row_pixels in glyph_center:
                # Print '#' for ink (values > 0.5), '.' for background
                # Cluster centers are averages, so pixels are float values between 0 and 1
                print("".join(['#' if p > 0.5 else '.' for p in row_pixels]), file=sys.stderr)
            print("-" * 20, file=sys.stderr)
        print("\nNow, update PRETRAINED_MAPPING in the script based on these visuals.", file=sys.stderr)
    # --- End Calibration Print ---

    hex_string = ''.join(PRETRAINED_MAPPING[label] for label in labels)
    return hex_string

def decode_with_bash_pipeline(hex_string):
    bash_commands = f'printf "%s" "{hex_string}" | xxd -p -r | gzip -9'

    result = subprocess.run(
        ["bash", "-i", "-l", "-c", bash_commands],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    sys.stdout.buffer.write(result.stdout)
    sys.stderr.write(result.stderr.decode(errors="replace"))
    sys.exit(result.returncode)

if __name__ == "__main__":
    args = sys.argv[1:]
    calibrate = "--calibrate" in args
    if calibrate:
        args.remove("--calibrate")
        print("Calibration mode", file=sys.stderr)
    if len(args) > 0:
        print("Unsupported arguments provided:", args, file=sys.stderr)
    gif_data = sys.stdin.buffer.read()
    hex_output = extract_hex_from_gif(gif_data, calibrate)
    if calibrate:
        print("Calibration complete. Update PRETRAINED_MAPPING in the script.", file=sys.stderr)
        sys.exit(0)
    else:
        # Decode the hex string using a bash pipeline
        decode_with_bash_pipeline(hex_output)
