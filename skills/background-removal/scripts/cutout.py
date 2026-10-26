#!/usr/bin/env python3
r"""Cut the background out of photos and write transparent PNGs.

Requires: pillow, numpy, rembg, onnxruntime

    python cutout.py "GB Out Port (45 deg).jpg"
    python cutout.py -o .\cutouts --max-width 1600 --webp .\photos\*.jpg

Each source becomes a sibling PNG named after it:

    GB Out Port (45 deg).jpg  ->  GB Out Port (45 deg, no background).png
    photo.jpg                 ->  photo (no background).png
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Keep sibling files in this folder from shadowing site-packages imports.
_HERE = Path(__file__).resolve().parent
sys.path[:] = [path for path in sys.path if Path(path or ".").resolve() != _HERE]

from PIL import Image, ImageOps  # noqa: E402
from rembg import new_session, remove  # noqa: E402

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
TRAILING_PAREN = re.compile(r"^(?P<base>.+?)\s*\((?P<inner>[^()]*)\)$")


def output_name(source: Path, label: str) -> str:
    """Insert the label into a trailing parenthetical, or append one."""
    stem = source.stem
    match = TRAILING_PAREN.match(stem)
    if match and match["inner"].strip():
        stem = f"{match['base']} ({match['inner']}, {label})"
    else:
        stem = f"{stem} ({label})"
    return f"{stem}.png"


def already_labelled(source: Path, label: str) -> bool:
    """True when the file name already marks the file as a cutout."""
    match = TRAILING_PAREN.match(source.stem)
    if not match:
        return False
    parts = [part.strip().lower() for part in match["inner"].split(",")]
    return label.strip().lower() in parts


def crop_to_alpha(image: Image.Image, threshold: int) -> Image.Image:
    """Trim the empty margin, ignoring near-invisible matte noise."""
    mask = image.getchannel("A").point(lambda value: 255 if value >= threshold else 0)
    box = mask.getbbox()
    if not box:
        raise ValueError("the alpha matte is empty; no subject was found")
    return image.crop(box)


def cutout(source: Path, args: argparse.Namespace, session) -> tuple[Path, Image.Image]:
    original = Image.open(source)
    original = ImageOps.exif_transpose(original)
    size = original.size
    image = original.convert("RGBA")

    image = remove(image, session=session, alpha_matting=args.alpha_matting)

    if not args.no_crop:
        image = crop_to_alpha(image, args.crop_threshold)

    if args.max_width and image.width > args.max_width:
        height = round(image.height * args.max_width / image.width)
        image = image.resize((args.max_width, height), Image.LANCZOS)

    if args.pad:
        image = ImageOps.expand(image, args.pad, fill=(0, 0, 0, 0))

    target = Path(args.out_dir or source.parent) / output_name(source, args.label)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, optimize=True)
    if args.webp:
        image.save(target.with_suffix(".webp"), "WEBP", quality=92, method=6)

    print(f"{source.name} -> {target.name}")
    print(f"    {image.width}x{image.height} (source {size[0]}x{size[1]}, matte {image.mode})")
    return target, image


def collect(sources: list[str], parser: argparse.ArgumentParser) -> list[Path]:
    files: list[Path] = []
    for raw in sources:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(p for p in path.iterdir() if p.suffix.lower() in SUPPORTED))
        elif path.is_file():
            files.append(path)
        else:
            parser.error(f"not a file or directory: {raw}")
    unique: list[Path] = []
    for path in files:
        if path not in unique:
            unique.append(path)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove the background from photos and write transparent PNGs.",
        epilog=(
            "Models: u2net (default), isnet-general-use, birefnet-general, "
            "u2net_human_seg. The first run downloads the model to ~/.u2net."
        ),
    )
    parser.add_argument("sources", nargs="+", metavar="FILE", help="image files or folders")
    parser.add_argument("-o", "--out-dir", help="output folder (default: beside each source)")
    parser.add_argument(
        "--label",
        default="no background",
        help='phrase added to the file name (default: "no background")',
    )
    parser.add_argument("--model", default="u2net", help="rembg model name (default: u2net)")
    parser.add_argument(
        "--alpha-matting",
        action="store_true",
        help="refine soft edges; slower, better on hair and fine detail",
    )
    parser.add_argument(
        "--max-width", type=int, default=0, help="downscale wider results; 0 keeps full size"
    )
    parser.add_argument("--pad", type=int, default=0, help="transparent padding in pixels")
    parser.add_argument(
        "--no-crop", action="store_true", help="keep the original frame instead of trimming"
    )
    parser.add_argument(
        "--crop-threshold",
        type=int,
        default=8,
        help="minimum alpha treated as subject when trimming (default: 8)",
    )
    parser.add_argument("--webp", action="store_true", help="also write a lossy-alpha WebP")
    parser.add_argument("--force", action="store_true", help="overwrite existing outputs")
    args = parser.parse_args()

    files = collect(args.sources, parser)
    if not files:
        parser.error("no supported image files found")

    for source in files:
        if already_labelled(source, args.label):
            print(f"{source.name} -> skipped, already a cutout")

    files = [source for source in files if not already_labelled(source, args.label)]
    pending = [
        source
        for source in files
        if args.force
        or not (Path(args.out_dir or source.parent) / output_name(source, args.label)).exists()
    ]
    for source in files:
        if source not in pending:
            print(f"{source.name} -> skipped, output already exists (use --force)")

    if not pending:
        return 0

    session = new_session(args.model)
    failures = 0
    for source in pending:
        try:
            cutout(source, args, session)
        except Exception as error:  # keep a batch going when one file fails
            failures += 1
            print(f"{source.name} -> failed: {error}", file=sys.stderr)

    if failures:
        print(f"{failures} of {len(pending)} files failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
