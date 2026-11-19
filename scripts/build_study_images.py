#!/usr/bin/env python3
"""Rebuild the 270 preprocessed study images from an upstream YESBUT download.

The bounding boxes in human_responses.csv and model_responses.csv are normalized
against these images, not against an upstream download. Run this script first if
you want to overlay, visualize, or re-measure those coordinates.

The preprocessed images are a derivative of a CC BY-NC-ND benchmark and are
therefore not redistributed. This script plus image_transform.csv regenerates
them byte-equivalently (up to JPEG requantization) from the original source.

Pipeline, per image:
  1. Scale the upstream image to width 1080, preserving aspect ratio.
  2. Take the vertical band [src_band_top, src_band_top + src_band_height) --
     the comic between its top and bottom border lines. Everything outside it
     is the YES / BUT heading text and surrounding margin, and is dropped.
  3. Paste that band onto a white 1080x1080 canvas at row dst_band_top.

Steps 1-3 are read from image_transform.csv rather than re-detected, so the
output matches the images participants and models actually saw. Pass --detect to
re-derive the band with the original border-detection heuristic instead.

Usage:
    python download_images.py --json_file data/YesBut_data.json \
                              --save_folder data/YesBut_images   # upstream repo
    python build_study_images.py --src data/YesBut_images --out study_images
    python build_study_images.py --src data/YesBut_images --out study_images \
                                 --verify reference_images
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

CANVAS = 1080
DARK = 200          # pixel value below which a pixel counts as ink
BORDER_FRAC = 0.80  # fraction of a row that must be ink to call it a border line


def detect_band(gray):
    """Original heuristic: scan in from the top and the bottom for the first row
    that is mostly ink -- the comic's horizontal border lines."""
    ink = (gray < DARK).mean(axis=1)
    rows = np.flatnonzero(ink >= BORDER_FRAC)
    if not len(rows):
        return None
    return int(rows[0]), int(rows[-1]) - int(rows[0]) + 1


def build(src_path, top, height, dst_top):
    img = Image.open(src_path).convert("RGB")
    if img.width != CANVAS:
        img = img.resize((CANVAS, round(img.height * CANVAS / img.width)), Image.LANCZOS)
    band = img.crop((0, top, CANVAS, min(top + height, img.height)))
    canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
    canvas.paste(band, (0, dst_top))
    return canvas


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, required=True,
                    help="folder of upstream YESBUT images (00001.jpg ...)")
    ap.add_argument("--out", type=Path, required=True, help="output folder")
    ap.add_argument("--manifest", type=Path,
                    default=Path(__file__).resolve().parent.parent / "image_transform.csv")
    ap.add_argument("--detect", action="store_true",
                    help="re-detect the band instead of using the manifest")
    ap.add_argument("--verify", type=Path,
                    help="folder of reference study images to compare against")
    ap.add_argument("--clean", action="store_true",
                    help="delete files in --out that this run did not write")
    args = ap.parse_args()

    rows = list(csv.DictReader(args.manifest.open(encoding="utf-8")))
    args.out.mkdir(parents=True, exist_ok=True)

    missing, diffs = [], []
    for row in rows:
        name = row["image_id"] + ".jpg"
        src = args.src / name
        if not src.exists():
            missing.append(name)
            continue

        if args.detect:
            img = Image.open(src).convert("L")
            if img.width != CANVAS:
                img = img.resize((CANVAS, round(img.height * CANVAS / img.width)), Image.LANCZOS)
            band = detect_band(np.asarray(img))
            if band is None:
                missing.append(f"{name} (no border detected)")
                continue
            top, height = band
            dst_top = (CANVAS - height) // 2
        else:
            top = int(row["src_band_top"])
            height = int(row["src_band_height"])
            dst_top = int(row["dst_band_top"])

        out_img = build(src, top, height, dst_top)
        out_img.save(args.out / name, quality=95)

        if args.verify:
            ref = args.verify / name
            if ref.exists():
                a = np.asarray(out_img, dtype=int)
                b = np.asarray(Image.open(ref).convert("RGB"), dtype=int)
                diffs.append((name, float(np.abs(a - b).mean())))

    written = {row["image_id"] + ".jpg" for row in rows} - set(missing)
    print(f"wrote {len(written)} images to {args.out}")
    if missing:
        print(f"missing or undetectable ({len(missing)}): {missing[:5]}", file=sys.stderr)

    # The output folder is not cleared before writing, so anything left over from an
    # earlier run -- or dropped in by hand -- would otherwise be silently counted as
    # part of the stimulus set.
    stale = sorted(f.name for f in args.out.iterdir()
                   if f.is_file() and f.name not in written and f.name != ".DS_Store")
    if stale:
        if args.clean:
            for name in stale:
                (args.out / name).unlink()
            print(f"removed {len(stale)} file(s) this run did not write")
        else:
            print(f"WARNING: {args.out} also holds {len(stale)} file(s) this run did not write, "
                  f"so it now contains {len(written) + len(stale)} files, not {len(written)}: "
                  f"{stale[:5]}{' ...' if len(stale) > 5 else ''}", file=sys.stderr)
            print("         re-run with --clean to remove them", file=sys.stderr)
    if diffs:
        worst = max(diffs, key=lambda d: d[1])
        mean = sum(d[1] for d in diffs) / len(diffs)
        print(f"verify: mean abs diff {mean:.2f}, worst {worst[0]} at {worst[1]:.2f}")
        print("  (values below ~8 are JPEG and resampling requantization noise, not a layout mismatch)")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
