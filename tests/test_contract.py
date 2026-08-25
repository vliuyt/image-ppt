from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicContractTests(unittest.TestCase):
    def run_command(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_public_release_contract(self) -> None:
        result = self.run_command("scripts/check_public_release.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_all_jsonl_rows_parse(self) -> None:
        for path in ROOT.rglob("*.jsonl"):
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if line.strip():
                    with self.subTest(path=path.name, line=line_number):
                        self.assertIsInstance(json.loads(line), dict)

    def test_planning_only_manifest_passes_planning_gate(self) -> None:
        result = self.run_command(
            "scripts/validate_deck.py",
            "--manifest",
            "examples/planning_only_manifest.jsonl",
            "--sources",
            "examples/source_ledger.json",
            "--style-contract",
            "examples/style_contract.md",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_planning_only_manifest_fails_full_completion_gate(self) -> None:
        result = self.run_command(
            "scripts/validate_deck.py",
            "--manifest",
            "examples/planning_only_manifest.jsonl",
            "--sources",
            "examples/source_ledger.json",
            "--style-contract",
            "examples/style_contract.md",
            "--research-brief",
            "examples/research_brief.md",
            "--require-complete",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("planning-only route cannot pass", result.stdout)

    def test_command_help(self) -> None:
        for script in (
            "scripts/validate_deck.py",
            "scripts/build_contact_sheet.py",
            "scripts/assemble_pdf.py",
        ):
            with self.subTest(script=script):
                result = self.run_command(script, "--help")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
