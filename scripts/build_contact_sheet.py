#!/usr/bin/env python3
"""Build a labeled contact sheet from slide images in manifest order."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--thumb-width", type=int, default=400)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.columns < 1 or args.thumb_width < 160:
            raise ValueError("columns must be positive and thumb-width must be at least 160")
        if args.output.exists() and not args.overwrite:
            raise FileExistsError(f"Output exists; pass --overwrite to replace it: {args.output}")
        rows = []
        for line_number, line in enumerate(args.manifest.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line"] = line_number
            rows.append(row)
        rows.sort(key=lambda row: row.get("order", 0))
        if not rows:
            raise ValueError("Manifest contains no slides")

        thumb_height = round(args.thumb_width * 9 / 16)
        label_height = 34
        gap = 18
        margin = 24
        row_count = math.ceil(len(rows) / args.columns)
        canvas_width = margin * 2 + args.columns * args.thumb_width + (args.columns - 1) * gap
        canvas_height = margin * 2 + row_count * (thumb_height + label_height) + (row_count - 1) * gap
        canvas = Image.new("RGB", (canvas_width, canvas_height), "#ECE8DF")
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()

        for index, row in enumerate(rows):
            slide_id = str(row.get("slide_id", f"line-{row['_line']}"))
            relative = Path(str(row.get("image", "")))
            if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "slides":
                raise ValueError(f"{slide_id} has an unsafe image path")
            image_path = args.manifest.parent / relative
            slides_root = (args.manifest.parent / "slides").resolve()
            if not image_path.resolve().is_relative_to(slides_root):
                raise ValueError(f"{slide_id} image resolves outside slides/: {image_path}")
            if not image_path.is_file():
                raise FileNotFoundError(f"{slide_id} image is missing: {image_path}")
            with Image.open(image_path) as source:
                thumb = ImageOps.fit(source.convert("RGB"), (args.thumb_width, thumb_height), method=Image.Resampling.LANCZOS)
            column = index % args.columns
            row_number = index // args.columns
            x = margin + column * (args.thumb_width + gap)
            y = margin + row_number * (thumb_height + label_height + gap)
            canvas.paste(thumb, (x, y))
            draw.rectangle((x, y, x + args.thumb_width - 1, y + thumb_height - 1), outline="#5A554D", width=1)
            label = f"{slide_id}  {row.get('status', 'unknown')}"
            draw.text((x, y + thumb_height + 9), label, fill="#282522", font=font)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(args.output)
        print(json.dumps({"ok": True, "slides": len(rows), "output": str(args.output)}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
