#!/usr/bin/env python3
"""Check the public Image-PPT package for contract, privacy, and release errors."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = {
    "SKILL.md",
    "manifest.json",
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
    "assets/hero.png",
    "references/runtime-support.md",
    "evals/trigger_cases.json",
    "evals/output/cases.jsonl",
    "examples/planning_only_manifest.jsonl",
    "reports/output_quality_scorecard.md",
    "reports/security_trust_report.md",
}
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".py", ".txt", ".yaml", ".yml"}
FORBIDDEN_PATTERNS = {
    "personal macOS path": re.compile(r"/" + r"Users/[^/\s]+/"),
    "personal Windows path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{16,}\b"),
    "private key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def load_json(path: Path, errors: list[str]) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"Invalid JSON: {path.relative_to(ROOT)}: {exc}")
        return None


def main() -> int:
    parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    for relative in sorted(REQUIRED_FILES):
        if not (ROOT / relative).is_file():
            fail(errors, f"Missing required file: {relative}")

    skill_path = ROOT / "SKILL.md"
    skill = skill_path.read_text(encoding="utf-8") if skill_path.is_file() else ""
    frontmatter = re.search(r"\A---\s*\n(.*?)\n---", skill, re.DOTALL)
    if not frontmatter:
        fail(errors, "SKILL.md needs YAML frontmatter")
    else:
        block = frontmatter.group(1)
        if not re.search(r"^name:\s*image-ppt\s*$", block, re.MULTILINE):
            fail(errors, "SKILL.md frontmatter name must be image-ppt")
        if "planning-only" not in block or "gpt-image-2" not in block:
            fail(errors, "SKILL.md description must expose the runtime capability boundary")

    manifest = load_json(ROOT / "manifest.json", errors)
    if isinstance(manifest, dict):
        if manifest.get("name") != "image-ppt":
            fail(errors, "manifest name must be image-ppt")
        if manifest.get("owner") != "vliuyt":
            fail(errors, "manifest owner must be vliuyt")
        if not re.fullmatch(r"\d+\.\d+\.\d+", str(manifest.get("version", ""))):
            fail(errors, "manifest version must use semantic versioning")
        support = manifest.get("runtime_support", {})
        if not isinstance(support, dict) or support.get("without_image_generation") != "planning-only":
            fail(errors, "manifest runtime_support must define planning-only degradation")

    contract_text = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8")
        for relative in ("README.md", "README.zh-CN.md", "references/runtime-support.md")
        if (ROOT / relative).is_file()
    )
    for term in ("codex-built-in", "openai-api", "planning-only", "gpt-image-2"):
        if term not in contract_text:
            fail(errors, f"Public runtime contract is missing: {term}")

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            warnings.append(f"Skipped non-UTF-8 text file: {path.relative_to(ROOT)}")
            continue
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(content):
                fail(errors, f"Found {label} in {path.relative_to(ROOT)}")

    payload = {"ok": not errors, "errors": errors, "warnings": warnings}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
