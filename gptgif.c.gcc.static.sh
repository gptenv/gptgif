#!/bin/bash
gcc-12 -Wall -O2 gptgif.c -o gptgif -static -lgif -static-libgcc
