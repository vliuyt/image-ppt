"""Integration regressions for the real image -> contact sheet -> PDF scripts.

Fixtures are deterministic local images; no image service or API key is used.
Poppler provides an independent PDF renderer so page-count success alone cannot
hide blank, reordered, cropped, or incorrectly composited pages.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("assemble_pdf", ROOT / "scripts/assemble_pdf.py")
assemble = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assemble)


class ImagePipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.deck = Path(self.temp.name)
        (self.deck / "slides").mkdir()
        self.manifest = self.deck / "deck_manifest.jsonl"
        self.colors = [(220, 30, 40), (30, 180, 60), (30, 60, 220)]
        self.rows = []
        for i, (mode, suffix) in enumerate(
            [("RGB", "png"), ("RGB", "jpg"), ("RGBA", "png")], 1
        ):
            image = Image.new(mode, (640, 360), self.colors[i - 1])
            draw = ImageDraw.Draw(image)
            # Distinct corner markers detect cropping and rotation.
            for box, color in [
                ((8, 8, 56, 56), "white"),
                ((584, 8, 632, 56), "black"),
                ((8, 304, 56, 352), "yellow"),
                ((584, 304, 632, 352), "cyan"),
            ]:
                draw.rectangle(box, fill=color)
            if mode == "RGBA":
                draw.rectangle((280, 140, 360, 220), fill=(0, 0, 0, 0))
            relative = f"slides/page-{i}.{suffix}"
            image.save(self.deck / relative)
            image.close()
            self.rows.append({
                "slide_id": f"P{i:02d}", "order": i, "status": "validated",
                "image": relative,
                "qa": dict.fromkeys(("text", "factual", "visual", "style"), True),
            })
        self.write_rows([self.rows[2], self.rows[0], self.rows[1]])

    def write_rows(self, rows):
        self.manifest.write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
        )

    def run_script(self, script, output, *extra):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script),
             "--manifest", str(self.manifest), "--output", str(output), *extra],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )

    def assert_color(self, image, xy, expected, tolerance=18):
        actual = image.convert("RGB").getpixel(xy)
        self.assertTrue(
            all(abs(a - b) <= tolerance for a, b in zip(actual, expected)),
            f"pixel {xy}: expected {expected}, found {actual}",
        )

    def assemble_pdf(self):
        output = self.deck / "deck.pdf"
        result = self.run_script("assemble_pdf.py", output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual(report["verification"], "verified 3 pages with pypdf")
        return output

    def test_contact_sheet_order_dimensions_and_labels(self):
        output = self.deck / "contact.png"
        result = self.run_script(
            "build_contact_sheet.py", output, "--columns", "2", "--thumb-width", "320"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["slides"], 3)
        with Image.open(output) as sheet:
            self.assertEqual(sheet.size, (706, 494))
            for i, (x, y) in enumerate([(24, 24), (362, 24), (24, 256)]):
                self.assert_color(sheet, (x + 80, y + 90), self.colors[i])
                # Each expected ASCII label must actually draw non-background pixels.
                label = sheet.crop((x, y + 180, x + 200, y + 214)).convert("RGB")
                self.assertTrue(any(low < 100 for low, high in label.getextrema()))
            # Current sheet behavior drops alpha; PDF behavior is tested separately.
            self.assert_color(sheet, (24 + 160, 256 + 90), (0, 0, 0))

    def test_pdf_page_order_geometry_content_and_alpha(self):
        self.assertIsNotNone(shutil.which("pdftoppm"), "Install poppler-utils for PDF regression tests")
        output = self.assemble_pdf()
        reader = PdfReader(output)
        self.assertEqual(len(reader.pages), 3)
        for page in reader.pages:
            self.assertAlmostEqual(float(page.mediabox.width), 640 * 72 / 150, places=3)
            self.assertAlmostEqual(float(page.mediabox.height), 360 * 72 / 150, places=3)
        prefix = self.deck / "render"
        result = subprocess.run(
            ["pdftoppm", "-r", "150", "-scale-to-x", "640", "-scale-to-y", "360",
             "-png", str(output), str(prefix)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        rendered = sorted(self.deck.glob("render-*.png"))
        self.assertEqual(len(rendered), 3)
        for i, path in enumerate(rendered):
            with Image.open(path) as image:
                self.assertEqual(image.size, (640, 360))
                self.assert_color(image, (160, 180), self.colors[i])
                for xy, color in [
                    ((32, 32), (255, 255, 255)), ((608, 32), (0, 0, 0)),
                    ((32, 328), (255, 255, 0)), ((608, 328), (0, 255, 255)),
                ]:
                    self.assert_color(image, xy, color)
                if i == 2:
                    self.assert_color(image, (320, 180), (255, 255, 255))

    def test_image_inspection_and_la_normalization(self):
        path = self.deck / "slides" / "la.png"
        with Image.new("LA", (640, 360), (0, 0)) as image:
            image.save(path)
        with assemble.normalized_rgb(path, 0.01) as image:
            self.assertEqual(image.mode, "RGB")
            self.assert_color(image, (320, 180), (255, 255, 255), 0)
        validator_spec = importlib.util.spec_from_file_location(
            "validate_deck", ROOT / "scripts/validate_deck.py"
        )
        validator = importlib.util.module_from_spec(validator_spec)
        validator_spec.loader.exec_module(validator)
        errors, hashes, warnings = [], {}, []
        for row in self.rows:
            validator.inspect_image(
                self.deck / row["image"], row["slide_id"], 0.01, errors, hashes, warnings
            )
        self.assertEqual(errors, [])
        bad = self.deck / "slides" / "bad.png"
        bad.write_bytes(b"not an image")
        validator.inspect_image(bad, "BAD", 0.01, errors, hashes, warnings)
        self.assertTrue(any("cannot be opened" in error for error in errors))

    def test_assembly_rejects_invalid_inputs(self):
        cases = [
            ("duplicate", lambda rows: rows[1].update(order=1), "continuous"),
            ("gap", lambda rows: rows[2].update(order=4), "continuous"),
            ("planned", lambda rows: rows[0].update(status="planned"), "not finalized"),
            ("qa", lambda rows: rows[0]["qa"].update(visual=False), "complete QA"),
            ("missing", lambda rows: rows[0].update(image="slides/missing.png"), "missing"),
            ("unsafe", lambda rows: rows[0].update(image="../outside.png"), "unsafe"),
        ]
        for name, mutate, expected in cases:
            with self.subTest(case=name):
                rows = json.loads(json.dumps(self.rows))
                mutate(rows)
                self.write_rows(rows)
                output = self.deck / f"{name}.pdf"
                result = self.run_script("assemble_pdf.py", output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, json.loads(result.stderr)["error"])
                self.assertFalse(output.exists())
        for name, content in [("corrupt", None), ("aspect", (640, 400))]:
            with self.subTest(case=name):
                path = self.deck / "slides" / f"{name}.png"
                if content:
                    with Image.new("RGB", content) as image:
                        image.save(path)
                else:
                    path.write_bytes(b"not an image")
                rows = json.loads(json.dumps(self.rows))
                rows[0]["image"] = f"slides/{name}.png"
                self.write_rows(rows)
                result = self.run_script("assemble_pdf.py", self.deck / f"{name}.pdf")
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(json.loads(result.stderr)["ok"])

    def test_page_count_verification_rejects_mismatch_and_invalid_pdf(self):
        output = self.assemble_pdf()
        self.assertEqual(assemble.verify_pdf_page_count(output, 3), "verified 3 pages with pypdf")
        with self.assertRaisesRegex(ValueError, "page count mismatch"):
            assemble.verify_pdf_page_count(output, 2)
        invalid = self.deck / "invalid.pdf"
        invalid.write_bytes(b"not a PDF")
        from pypdf.errors import PdfReadError
        with self.assertLogs("pypdf", level="WARNING"):
            with self.assertRaises(PdfReadError):
                assemble.verify_pdf_page_count(invalid, 3)

    def test_existing_outputs_are_not_overwritten(self):
        self.write_rows(self.rows)
        for script, suffix in [
            ("assemble_pdf.py", "pdf"), ("build_contact_sheet.py", "png")
        ]:
            with self.subTest(script=script):
                output = self.deck / f"existing.{suffix}"
                output.write_bytes(b"preserve")
                result = self.run_script(script, output)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(output.read_bytes(), b"preserve")


if __name__ == "__main__":
    unittest.main()
