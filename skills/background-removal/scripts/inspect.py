#!/usr/bin/env python3
"""Check a transparent PNG's matte and render previews over several backgrounds.

Requires: pillow, numpy

    python inspect.py "GB Out Port (45 deg, no background).png"

Prints alpha statistics, flags leftover light background in the soft edge, and
writes a preview sheet (black, white, green panels) next to the temp folder.
Read the preview images; the numbers alone do not prove the matte looks right.
"""

from __future__ import annotations

import argparse
import glob
import sys
import tempfile
from pathlib import Path

# Keep sibling files in this folder from shadowing site-packages imports.
_HERE = Path(__file__).resolve().parent
sys.path[:] = [path for path in sys.path if Path(path or ".").resolve() != _HERE]

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

BACKGROUNDS = [(0, 0, 0), (255, 255, 255), (0, 140, 60)]
IMAGE_SUFFIXES = {".png", ".webp"}
GAP = 8
SPILL_LUMINANCE = 200
SPILL_TOLERANCE = 0.0005


def alpha_of(image: Image.Image) -> np.ndarray:
    if "A" in image.getbands():
        return np.asarray(image.getchannel("A"))
    return np.full((image.height, image.width), 255, dtype=np.uint8)


def edges_touched(alpha: np.ndarray) -> list[str]:
    hits = []
    if (alpha[0, :] >= 200).any():
        hits.append("top")
    if (alpha[-1, :] >= 200).any():
        hits.append("bottom")
    if (alpha[:, 0] >= 200).any():
        hits.append("left")
    if (alpha[:, -1] >= 200).any():
        hits.append("right")
    return hits


def collect(inputs: list[str], parser: argparse.ArgumentParser) -> list[Path]:
    files: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES))
        elif any(char in raw for char in "*?["):
            files.extend(sorted(Path(match) for match in glob.glob(raw)))
        elif path.is_file():
            files.append(path)
        else:
            parser.error(f"not a file, folder, or pattern: {raw}")
    unique: list[Path] = []
    for path in files:
        if path.is_file() and path not in unique:
            unique.append(path)
    return unique


def report(path: Path, image: Image.Image, warnings: list[str]) -> None:
    alpha = alpha_of(image)
    total = alpha.size
    transparent = float((alpha == 0).sum()) / total
    opaque = float((alpha >= 250).sum()) / total
    soft = (alpha > 0) & (alpha < 250)
    soft_count = int(soft.sum())

    print(f"{path.name}")
    print(f"    {image.width}x{image.height} {image.mode}")

    if "A" not in image.getbands():
        warnings.append("no alpha channel; the background was not removed")
        print("    no alpha channel")
        return
    if opaque >= 0.999:
        warnings.append("matte is fully opaque; the background was not removed")
    if transparent >= 0.999:
        warnings.append("matte is fully transparent; no subject was found")

    print(
        f"    transparent {transparent:.1%}  soft edge {soft_count / total:.2%}  "
        f"opaque {opaque:.1%}"
    )

    if soft_count:
        luminance = np.asarray(image.convert("RGB")).astype(int).mean(axis=2)
        spill = soft & (luminance >= SPILL_LUMINANCE)
        spill_count = int(spill.sum())
        print(f"    soft-edge mean luminance {luminance[soft].mean():.0f}")
        if spill_count:
            rows, cols = np.nonzero(spill)
            print(
                f"    light spill: {spill_count} px "
                f"(x {cols.min()}-{cols.max()}, y {rows.min()}-{rows.max()})"
            )
            if spill_count / total > SPILL_TOLERANCE:
                warnings.append(
                    f"{spill_count} light background pixels remain in the soft edge; "
                    "rerun with --alpha-matting or trim with a higher --crop-threshold"
                )
        else:
            print("    light spill: none")

    touched = edges_touched(alpha)
    print(f"    subject reaches: {', '.join(touched) if touched else 'no frame edge'}")


def preview(image: Image.Image, path: Path, height: int) -> None:
    scale = min(1.0, height / image.height)
    panel = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.LANCZOS,
    ).convert("RGBA")
    width = panel.width * len(BACKGROUNDS) + GAP * (len(BACKGROUNDS) - 1)
    sheet = Image.new("RGBA", (width, panel.height), (24, 24, 24, 255))
    offset = 0
    for color in BACKGROUNDS:
        backdrop = Image.new("RGBA", panel.size, color + (255,))
        backdrop.alpha_composite(panel)
        sheet.paste(backdrop, (offset, 0))
        offset += panel.width + GAP
    sheet.convert("RGB").save(path)


def preview_name(path: Path, out_dir: Path) -> Path:
    tag = "" if path.suffix.lower() == ".png" else f"-{path.suffix.lower().lstrip('.')}"
    return out_dir / f"{path.stem}{tag}-preview.png"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a cutout's alpha matte.")
    parser.add_argument("images", nargs="+", metavar="FILE", help="transparent image files")
    parser.add_argument(
        "--out-dir",
        help="where to write preview sheets (default: a cutout-previews folder in temp)",
    )
    parser.add_argument(
        "--height", type=int, default=640, help="preview panel height in pixels (default: 640)"
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else Path(tempfile.gettempdir()) / "cutout-previews"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = collect(args.images, parser)
    if not files:
        parser.error("no image files found")

    warnings: list[str] = []
    for path in files:
        image = Image.open(path)
        report(path, image, warnings)
        sheet = preview_name(path, out_dir)
        preview(image, sheet, args.height)
        print(f"    preview: {sheet}")
        print()

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"    - {warning}")
        return 1
    print("All mattes passed the checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
