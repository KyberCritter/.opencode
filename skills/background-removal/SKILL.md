---
name: background-removal
description: 'Use when an image needs its background removed or a transparent cutout is requested. Runs rembg on photos, trims the empty margin, writes a transparent PNG beside each source named "<name> (no background)", then verifies the matte over black, white, and green and previews the result.'
---

# Background Removal

Turn photos into transparent PNG cutouts with `rembg`, then prove the matte is clean by looking
at it over several backgrounds. The pipeline matches the hardware-photo workflow in
`GBScribe-Emulated/docs/asset-conversion.md`: RGBA, model matte, trim to the subject, transparent
PNG.

**Definition of done:** every requested image has a transparent `.png` next to it, the matte has no
light halo and no leftover background, nothing on the subject is clipped, and the previews have been
shown to the user.

## 1. Confirm the toolchain

```powershell
python -c "import rembg, onnxruntime, PIL, numpy"
```

If that fails:

```powershell
python -m pip install pillow numpy rembg onnxruntime
```

`rembg` downloads the model on first use (about 176 MB, into `%USERPROFILE%\.rembg\models`), so the
first run is slow. Later runs reuse it.

## 2. Run the cutout

```powershell
$skill = "D:\Coding\.opencode\skills\background-removal"
python "$skill\scripts\cutout.py" "E:\path\to\photo.jpg"
```

Files, folders, and patterns are all accepted, and one model session is reused for the batch:

```powershell
python "$skill\scripts\cutout.py" .\photos -o .\cutouts --max-width 1600 --webp
```

What the script does to each source:

1. Opens it with Pillow, applies EXIF rotation, converts to RGBA.
2. Builds the alpha matte with `rembg.remove()`.
3. Trims the empty margin at alpha >= `--crop-threshold` (default 8) so matte noise does not inflate the frame.
4. Optionally downscales to `--max-width` with LANCZOS, then adds `--pad` transparent pixels.
5. Writes `<name>.png` next to the source, plus a lossy-alpha WebP with `--webp`.

Default behaviour keeps full resolution, never upscales, and never touches the source file. Run
`python "$skill\scripts\cutout.py" --help` for every option.

## 3. Verify the matte

```powershell
python "$skill\scripts\inspect.py" ".\cutouts"
```

It prints alpha coverage, soft-edge luminance, any light spill with its location, and which frame
edges the subject reaches, then writes a preview sheet of the cutout over black, white, and green.

```text
GB Pocket Out Port (45 deg, no background).png
    1721x1778 RGBA
    transparent 43.6%  soft edge 3.04%  opaque 53.3%
    soft-edge mean luminance 39
    light spill: none
    subject reaches: left
    preview: C:\Users\...\Temp\cutout-previews\GB Pocket Out Port (45 deg, no background)-preview.png
```

Open every preview sheet with the file-reading tool and check:

- Dark edges show no beige or grey haze on the white panel and no bright rim on the black panel.
- The background is gone everywhere, including vignettes, tabletop gradients, and cast shadows.
- The subject is not clipped where it leaves the frame; `subject reaches:` should name exactly those edges.
- `light spill: none` unless the subject itself is white and glossy.
- Holes such as ports, slots, and grips are transparent, not filled with grey.

## 4. Show the result

Open each output PNG in the user's Review pane with the browser preview tool. Name the files and
their pixel sizes in the reply, and state which checks passed.

## 5. Fix what the previews reveal

| Symptom | Fix |
| --- | --- |
| Light halo or fringe on dark edges | Rerun with `--alpha-matting`; it is slower but resolves fine edges better |
| Faint haze ring, matte reads too soft | Rerun with a higher `--crop-threshold` such as 24 |
| Subject chunks missing or background kept | Try `--model isnet-general-use` or `--model birefnet-general` |
| Shiny or translucent subject loses its edge | `--alpha-matting` plus the same `--model` that handled the body best |
| Subject clipped where it meets the frame edge | `--no-crop` to keep the original frame |
| Teeth, hair, or cable strands look chewed | `--alpha-matting` at full resolution, no `--max-width` |
| Output too heavy for a web page | `--max-width 1200 --webp` |
| Everything transparent | The model found nothing; try another `--model` and confirm the file opens |

If two models disagree, keep both candidates as separate outputs and compare the preview sheets
rather than guessing.

## 6. Naming and re-runs

| Source | Output |
| --- | --- |
| `GB Out Port (45 deg).jpg` | `GB Out Port (45 deg, no background).png` |
| `photo.jpg` | `photo (no background).png` |

- The label is inserted into an existing trailing parenthetical, otherwise appended in a new one.
- `--label "cutout"` changes the phrase; outputs always end in `.png`.
- Outputs land beside the source unless `-o/--out-dir` is given.
- Files that already carry the label, and outputs that already exist, are skipped; `--force` overwrites.
- The script is idempotent: rerunning a folder only processes new images.

## Guardrails

- Never overwrite or delete a source image; every run creates new files.
- Keep the subject at full resolution unless the user asks for a web-sized asset.
- Do not accept statistics alone as proof; read the preview sheets before reporting success.
- Do not ship a haloed cutout. If no model produces a clean matte, show the preview sheet and report the exact failure.
- Preserve the subject's proportions; the only crop allowed is the transparent-margin trim.
