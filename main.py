#!/usr/bin/env python3
"""Ship the rendered poster into the grader's output directory.

The poster is drawn locally by draw.py (Pillow plus the DejaVu fonts)
and committed as entry.png next to this file; this program only copies
that file. The split is deliberate: the grader runs this program in the
competition's pinned python:3.13-slim image, which ships neither Pillow
nor any font, and with no network to fetch them -- so a program that
tries to draw here fails on import before it draws a pixel. This file
therefore uses only the standard library, so it runs anywhere Python 3
does.

Output directory, in order:
  1. $MAKEFUN_OUTPUT_DIR (what the kit uses locally)
  2. /output (what the grader provides)
  3. the current working directory (fallback for a manual run)

After copying it verifies the copy: same byte size and sha256 as the
poster in this repository, a whole PNG of 1024x1024 pixels, at most
1 MiB. If the output directory is the poster's own directory, the copy
is a no-op and only the verification runs.
"""

import hashlib
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
POSTER_NAME = "entry.png"
EXPECTED_SIZE = (1024, 1024)
MAX_BYTES = 1024 * 1024


def resolve_output_dir():
    """Pick where entry.png goes, preferring the kit/grader locations."""
    for candidate in (os.environ.get("MAKEFUN_OUTPUT_DIR"), "/output", "."):
        if not candidate:
            continue
        if os.path.isdir(candidate) and os.access(candidate, os.W_OK):
            return candidate
    # Last resort: create ./out next to the program.
    fallback = os.path.join(HERE, "out")
    os.makedirs(fallback, exist_ok=True)
    return fallback


def _digest(path):
    """SHA-256 of a file, read in 1 MiB chunks."""
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _png_dimensions(path):
    """Width and height from a PNG's IHDR chunk; raises on bad data."""
    with open(path, "rb") as handle:
        head = handle.read(33)
    if len(head) < 33 or head[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("not a PNG: %s" % path)
    if head[12:16] != b"IHDR":
        raise SystemExit("no IHDR chunk: %s" % path)
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def ship_poster():
    """Copy the committed poster to the output directory and verify it."""
    source = os.path.join(HERE, POSTER_NAME)
    if not os.path.isfile(source):
        print("missing poster: %s (run draw.py first)" % source,
              file=sys.stderr)
        return 1
    out_dir = resolve_output_dir()
    destination = os.path.join(out_dir, POSTER_NAME)
    if os.path.abspath(source) != os.path.abspath(destination):
        shutil.copyfile(source, destination)
    src_bytes = os.path.getsize(source)
    dst_bytes = os.path.getsize(destination)
    if src_bytes != dst_bytes:
        print("size mismatch after copy: %d vs %d" % (src_bytes, dst_bytes),
              file=sys.stderr)
        return 1
    if src_bytes > MAX_BYTES:
        print("poster too big: %d bytes" % src_bytes, file=sys.stderr)
        return 1
    if _digest(source) != _digest(destination):
        print("hash mismatch after copy", file=sys.stderr)
        return 1
    width, height = _png_dimensions(destination)
    if (width, height) != EXPECTED_SIZE:
        print("poster is %dx%d, want 1024x1024" % (width, height),
              file=sys.stderr)
        return 1
    print("shipped %s -> %s (%d bytes, sha256 %s)"
          % (source, destination, dst_bytes, _digest(destination)))
    return 0


if __name__ == "__main__":
    sys.exit(ship_poster())
