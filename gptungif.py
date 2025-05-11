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
import os
import io
import numpy as np
from PIL import Image, ImageSequence
import subprocess
import tempfile
from sklearn.cluster import KMeans
import argparse

GLYPH_WIDTH = 8
GLYPH_HEIGHT = 8

def extract_hex_from_gif(gif_bytes, cluster_map, calibrate=False):
    gif_image = Image.open(io.BytesIO(gif_bytes))
    glyph_tiles = []
    extraction_halted = False

    for frame in ImageSequence.Iterator(gif_image):
        if extraction_halted:
            break
        grayscale = frame.convert("L")
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
                if np.sum(glyph) < 5:
                    extraction_halted = True
                    break
                glyph_tiles.append(glyph)

    flat_tiles = [np.ravel(np.ascontiguousarray(tile)) for tile in glyph_tiles]
    X = np.stack(flat_tiles)
    kmeans = KMeans(n_clusters=len(cluster_map), random_state=0, n_init=10)
    labels = kmeans.fit_predict(X)

    if calibrate:
        print("K-Means Cluster Centroids (visualized as 8x8 glyphs):", file=sys.stderr)
        for i, center_vector in enumerate(kmeans.cluster_centers_):
            print(f"\nCluster Label: {i}", file=sys.stderr)
            glyph_center = center_vector.reshape(GLYPH_HEIGHT, GLYPH_WIDTH)
            for row_pixels in glyph_center:
                print("".join(['#' if p > 0.5 else '.' for p in row_pixels]), file=sys.stderr)
            print("-" * 20, file=sys.stderr)
        print("\nNow associate each index with the correct character from the cluster map.", file=sys.stderr)

    hex_string = ''.join(cluster_map[label] for label in labels)
    return hex_string

def decode_with_bash_pipeline(hex_string):
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".hex") as hex_string_file:
        hex_string_file.write(hex_string)
        hex_string_file_path = hex_string_file.name

    bash_script = f"xxd -p -r < {hex_string_file_path} | gzip -9"
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as script_file:
        script_file.write(bash_script)
        script_path = script_file.name

    result = subprocess.run(
        ["bash", "-i", "-l", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    os.unlink(script_path)
    os.unlink(hex_string_file_path)

    try:
        sys.stdout.buffer.write(result.stdout)
        sys.stderr.write(result.stderr.decode(errors="replace"))
    except Exception as err:
        print(f"Exception during output: {err}", file=sys.stderr)
        print(result.stdout)
        print(result.stderr.decode(errors="replace"), file=sys.stderr)

    sys.exit(result.returncode)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode a .gptgif with optional cluster-map override.")
    parser.add_argument("--calibrate", action="store_true", help="Run in calibration mode.")
    parser.add_argument("--cluster-map", type=str, help="ASCII characters ordered by cluster index (use 0x... for hex)")
    args = parser.parse_args()

    if args.cluster_map:
        raw = args.cluster_map
        if raw.startswith("0x"):
            cluster_map = raw[2:]
        else:
            cluster_map = raw
    else:
        cluster_map = "0123456789abcdef"
        print("Warning: --cluster-map not specified. Defaulting to '0123456789abcdef'", file=sys.stderr)

    try:
        gif_data = sys.stdin.buffer.read()
        hex_output = extract_hex_from_gif(gif_data, cluster_map, args.calibrate)
        if args.calibrate:
            print("Calibration complete.", file=sys.stderr)
            sys.exit(0)
        else:
            decode_with_bash_pipeline(hex_output)
    except Exception as err:
        print(f"Exception during processing: {err}", file=sys.stderr)
        raise
