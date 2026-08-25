#!/usr/bin/env python3
"""Assemble validated image-first deck pages into an ordered PDF."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image


FINAL_STATUSES = {"validated", "fallback-typeset"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Path to deck_manifest.jsonl")
    parser.add_argument("--output", type=Path, required=True, help="Destination PDF")
    parser.add_argument("--aspect-tolerance", type=float, default=0.01)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_manifest(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at line {line_number}: column {exc.colno}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"Manifest line {line_number} must be a JSON object")
        rows.append(row)
    if not rows:
        raise ValueError("Manifest contains no slides")
    return sorted(rows, key=lambda row: row.get("order", 0))


def normalized_rgb(image_path: Path, tolerance: float) -> Image.Image:
    with Image.open(image_path) as source:
        width, height = source.size
        if height <= 0 or abs((width / height) - (16 / 9)) > tolerance:
            raise ValueError(f"{image_path} is {width}x{height}, outside the 16:9 tolerance")
        if source.mode in {"RGBA", "LA"}:
            background = Image.new("RGB", source.size, "white")
            alpha = source.getchannel("A")
            background.paste(source.convert("RGB"), mask=alpha)
            return background
        return source.convert("RGB").copy()


def verify_pdf_page_count(path: Path, expected: int) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return "pypdf unavailable; page count inferred from the ordered input set"
    actual = len(PdfReader(str(path)).pages)
    if actual != expected:
        raise ValueError(f"PDF page count mismatch: expected {expected}, found {actual}")
    return f"verified {actual} pages with pypdf"


def main() -> int:
    args = parse_args()
    pages: list[Image.Image] = []
    try:
        if args.output.exists() and not args.overwrite:
            raise FileExistsError(f"Output exists; pass --overwrite to replace it: {args.output}")
        rows = load_manifest(args.manifest)
        expected_orders = list(range(1, len(rows) + 1))
        actual_orders = [row.get("order") for row in rows]
        if actual_orders != expected_orders:
            raise ValueError("Slide order must be continuous from 1")

        for row in rows:
            slide_id = row.get("slide_id", f"P{row.get('order', 0):02d}")
            if row.get("status") not in FINAL_STATUSES:
                raise ValueError(f"{slide_id} is not finalized: {row.get('status')}")
            qa = row.get("qa", {})
            if not all(qa.get(field) is True for field in ("text", "factual", "visual", "style")):
                raise ValueError(f"{slide_id} does not have complete QA")
            relative = Path(str(row.get("image", "")))
            if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "slides":
                raise ValueError(f"{slide_id} has an unsafe image path")
            image_path = args.manifest.parent / relative
            slides_root = (args.manifest.parent / "slides").resolve()
            if not image_path.resolve().is_relative_to(slides_root):
                raise ValueError(f"{slide_id} image resolves outside slides/: {image_path}")
            if not image_path.is_file():
                raise FileNotFoundError(f"{slide_id} image is missing: {image_path}")
            pages.append(normalized_rgb(image_path, args.aspect_tolerance))

        args.output.parent.mkdir(parents=True, exist_ok=True)
        first, rest = pages[0], pages[1:]
        first.save(args.output, "PDF", save_all=True, append_images=rest, resolution=150.0)
        verification = verify_pdf_page_count(args.output, len(rows))
        print(json.dumps({"ok": True, "pages": len(rows), "output": str(args.output), "verification": verification}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        for page in pages:
            page.close()


if __name__ == "__main__":
    sys.exit(main())
