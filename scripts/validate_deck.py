#!/usr/bin/env python3
"""Validate an Image-PPT source ledger, style contract, manifest, and slide files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


FINAL_STATUSES = {"validated", "fallback-typeset"}
ALLOWED_STATUSES = FINAL_STATUSES | {"planned", "generated", "failed"}
ALLOWED_ROUTES = {"codex-built-in-gpt-image-2", "openai-api-gpt-image-2", "planning-only"}
ALLOWED_ROLES = {
    "cover",
    "section",
    "factual",
    "narrative",
    "map",
    "relationship",
    "timeline",
    "comparison",
    "summary",
    "sources",
}
ALLOWED_SOURCE_KINDS = {
    "primary",
    "later-tradition",
    "scholarship",
    "official-current",
    "context",
}
ALLOWED_SUPPORT_TYPES = {"direct", "synthesis", "contested"}
REQUIRED_SLIDE_FIELDS = {
    "slide_id",
    "order",
    "title",
    "role",
    "takeaway",
    "visible_text",
    "requires_sources",
    "claim_ids",
    "source_ids",
    "prototype",
    "style_reference_ids",
    "prompt",
    "model_route",
    "api_authorized",
    "status",
    "image",
    "attempts",
    "qa",
}
QA_FIELDS = {"text", "factual", "visual", "style"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Path to deck_manifest.jsonl")
    parser.add_argument("--sources", type=Path, required=True, help="Path to source_ledger.json")
    parser.add_argument("--style-contract", type=Path, help="Path to style_contract.md; defaults beside the manifest")
    parser.add_argument(
        "--research-brief",
        type=Path,
        help="Path to research_brief.md; required for --require-complete and defaults to research/research_brief.md",
    )
    parser.add_argument("--check-files", action="store_true", help="Inspect slide files referenced by the manifest")
    parser.add_argument("--require-complete", action="store_true", help="Require every slide to have a final status and passing QA")
    parser.add_argument("--aspect-tolerance", type=float, default=0.01, help="Allowed deviation from 16:9")
    parser.add_argument("--json-output", type=Path, help="Optional machine-readable report path")
    return parser.parse_args()


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"Missing file: {path}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"Expected a JSON object in {path}")
        return {}
    return value


def load_manifest(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"Missing file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSONL at line {line_number}: column {exc.colno}")
            continue
        if not isinstance(row, dict):
            errors.append(f"Manifest line {line_number} must be a JSON object")
            continue
        row["_line"] = line_number
        rows.append(row)
    if not rows:
        errors.append("Manifest contains no slide rows")
    return rows


def duplicate_values(items: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return sorted(duplicates)


def is_string_list(value: Any, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
    )


def validate_ledger(
    ledger: dict[str, Any], errors: list[str], warnings: list[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if ledger.get("research_mode") not in {"source-locked", "research-backed", "editorial"}:
        errors.append("source_ledger.json needs a valid research_mode")
    if not str(ledger.get("content_boundary", "")).strip():
        errors.append("source_ledger.json needs a non-empty content_boundary")

    sources_raw = ledger.get("sources", [])
    claims_raw = ledger.get("claims", [])
    if not isinstance(sources_raw, list) or not sources_raw:
        errors.append("source_ledger.json needs a non-empty sources array")
        sources_raw = []
    if not isinstance(claims_raw, list):
        errors.append("source_ledger.json claims must be an array")
        claims_raw = []

    source_ids = [str(item.get("id", "")) for item in sources_raw if isinstance(item, dict)]
    claim_ids = [str(item.get("id", "")) for item in claims_raw if isinstance(item, dict)]
    for duplicate in duplicate_values(source_ids):
        errors.append(f"Duplicate source ID: {duplicate}")
    for duplicate in duplicate_values(claim_ids):
        errors.append(f"Duplicate claim ID: {duplicate}")

    sources: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(sources_raw, start=1):
        if not isinstance(source, dict):
            errors.append(f"Source {index} must be an object")
            continue
        source_id = str(source.get("id", "")).strip()
        if not re.fullmatch(r"SRC-\d{3,}", source_id):
            errors.append(f"Source {index} has invalid ID: {source_id or '<empty>'}")
        if not isinstance(source.get("kind"), str) or source.get("kind") not in ALLOWED_SOURCE_KINDS:
            errors.append(f"{source_id or f'Source {index}'} has invalid kind")
        for field in ("title", "location"):
            if not str(source.get(field, "")).strip():
                errors.append(f"{source_id or f'Source {index}'} is missing {field}")
        if source.get("kind") == "primary" and not str(source.get("edition_or_date", "")).strip():
            errors.append(f"{source_id or f'Source {index}'} primary source needs edition_or_date")
        if source.get("kind") == "official-current" and not str(source.get("accessed", "")).strip():
            errors.append(f"{source_id or f'Source {index}'} official-current source needs accessed")
        if source_id:
            sources[source_id] = source

    claims: dict[str, dict[str, Any]] = {}
    for index, claim in enumerate(claims_raw, start=1):
        if not isinstance(claim, dict):
            errors.append(f"Claim {index} must be an object")
            continue
        claim_id = str(claim.get("id", "")).strip()
        if not re.fullmatch(r"CLM-\d{3,}", claim_id):
            errors.append(f"Claim {index} has invalid ID: {claim_id or '<empty>'}")
        if not str(claim.get("text", "")).strip():
            errors.append(f"{claim_id or f'Claim {index}'} is missing text")
        referenced = claim.get("source_ids", [])
        if not is_string_list(referenced, allow_empty=False):
            errors.append(f"{claim_id or f'Claim {index}'} needs source_ids")
            referenced = []
        for source_id in referenced:
            if source_id not in sources:
                errors.append(f"{claim_id or f'Claim {index}'} references unknown source {source_id}")
        if not isinstance(claim.get("confidence"), str) or claim.get("confidence") not in {"high", "medium", "low"}:
            errors.append(f"{claim_id or f'Claim {index}'} has invalid confidence")
        if not isinstance(claim.get("source_layer"), str) or claim.get("source_layer") not in ALLOWED_SOURCE_KINDS:
            errors.append(f"{claim_id or f'Claim {index}'} has invalid source_layer")
        support_type = claim.get("support_type")
        if not isinstance(support_type, str) or support_type not in ALLOWED_SUPPORT_TYPES:
            errors.append(f"{claim_id or f'Claim {index}'} has invalid support_type")
        if support_type == "synthesis" and len(referenced) < 2:
            errors.append(f"{claim_id or f'Claim {index}'} synthesis needs at least two sources")
        if support_type == "contested" and not str(claim.get("caveat", "")).strip():
            errors.append(f"{claim_id or f'Claim {index}'} contested claim needs a caveat")
        if claim.get("confidence") in {"medium", "low"} and not str(claim.get("caveat", "")).strip():
            errors.append(f"{claim_id or f'Claim {index}'} {claim.get('confidence')}-confidence claim needs a caveat")
        allowed_slides = claim.get("allowed_slides", [])
        if not isinstance(allowed_slides, list) or any(
            not isinstance(value, int) or isinstance(value, bool) or value < 1 for value in allowed_slides
        ):
            errors.append(f"{claim_id or f'Claim {index}'} allowed_slides must contain positive integers")
            allowed_slides = []
        if claim_id:
            normalized_claim = dict(claim)
            normalized_claim["source_ids"] = referenced
            normalized_claim["allowed_slides"] = allowed_slides
            claims[claim_id] = normalized_claim
    return sources, claims


def safe_relative_image(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts and path.parts[0] == "slides"


def inspect_image(
    image_path: Path,
    slide_id: str,
    tolerance: float,
    errors: list[str],
    hashes: dict[str, str],
    warnings: list[str],
) -> None:
    try:
        from PIL import Image
    except ImportError:
        errors.append("Pillow is required for --check-files")
        return
    if not image_path.is_file():
        errors.append(f"{slide_id} image is missing: {image_path}")
        return
    try:
        with Image.open(image_path) as image:
            width, height = image.size
            image.verify()
    except Exception as exc:  # Pillow exposes multiple format-specific errors.
        errors.append(f"{slide_id} image cannot be opened: {exc}")
        return
    if height <= 0 or abs((width / height) - (16 / 9)) > tolerance:
        errors.append(f"{slide_id} is {width}x{height}, outside the 16:9 tolerance")
    digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
    if digest in hashes:
        warnings.append(f"{slide_id} duplicates the bytes of {hashes[digest]}")
    else:
        hashes[digest] = slide_id


def validate_manifest(
    rows: list[dict[str, Any]],
    sources: dict[str, dict[str, Any]],
    claims: dict[str, dict[str, Any]],
    manifest_path: Path,
    check_files: bool,
    require_complete: bool,
    tolerance: float,
    errors: list[str],
    warnings: list[str],
) -> tuple[set[str], set[str], set[str]]:
    ids = [str(row.get("slide_id", "")) for row in rows]
    for duplicate in duplicate_values(ids):
        errors.append(f"Duplicate slide ID: {duplicate}")

    orders = [row.get("order") for row in rows]
    if any(not isinstance(order, int) or isinstance(order, bool) for order in orders):
        errors.append("Every slide order must be an integer")
    elif sorted(orders) != list(range(1, len(rows) + 1)):
        errors.append("Slide order must be unique and continuous from 1")

    prototype_ids = {
        str(row.get("slide_id", ""))
        for row in rows
        if row.get("prototype") is True
    }
    if len(rows) >= 3 and len(prototype_ids) < 3:
        errors.append("A deck with three or more slides needs at least three style prototypes")
    prototype_roles = {
        str(row.get("role", ""))
        for row in rows
        if row.get("prototype") is True
    }
    if len(rows) >= 3:
        if "cover" not in prototype_roles:
            errors.append("Style prototypes must include a cover")
        if not prototype_roles & {"factual", "map", "relationship", "timeline", "comparison"}:
            errors.append("Style prototypes must include a dense factual or diagram page")
        if not prototype_roles & {"narrative", "section", "summary"}:
            errors.append("Style prototypes must include a narrative or section page")

    image_hashes: dict[str, str] = {}
    used_claim_ids: set[str] = set()
    used_source_ids: set[str] = set()
    for row in rows:
        line = row.get("_line", "?")
        slide_id = str(row.get("slide_id", f"line-{line}"))
        missing = sorted(REQUIRED_SLIDE_FIELDS - row.keys())
        if missing:
            errors.append(f"{slide_id} is missing fields: {', '.join(missing)}")
            continue
        order = row["order"]
        expected_id = f"P{order:02d}" if isinstance(order, int) else ""
        if slide_id != expected_id:
            errors.append(f"Manifest line {line} slide_id should be {expected_id}, found {slide_id}")
        if not isinstance(row["role"], str) or row["role"] not in ALLOWED_ROLES:
            errors.append(f"{slide_id} has invalid role: {row['role']}")
        if not str(row["title"]).strip() or not str(row["takeaway"]).strip():
            errors.append(f"{slide_id} needs a title and takeaway")
        if not is_string_list(row["visible_text"], allow_empty=False):
            errors.append(f"{slide_id} visible_text must be a non-empty array")
        if not str(row["prompt"]).strip():
            errors.append(f"{slide_id} needs a generation prompt")
        if not isinstance(row["requires_sources"], bool):
            errors.append(f"{slide_id} requires_sources must be boolean")

        source_ids = row["source_ids"] if is_string_list(row["source_ids"]) else []
        claim_ids = row["claim_ids"] if is_string_list(row["claim_ids"]) else []
        if not is_string_list(row["source_ids"]):
            errors.append(f"{slide_id} source_ids must contain only non-empty strings")
        if not is_string_list(row["claim_ids"]):
            errors.append(f"{slide_id} claim_ids must contain only non-empty strings")
        used_source_ids.update(source_ids)
        used_claim_ids.update(claim_ids)
        if row["requires_sources"] is True and (not source_ids or not claim_ids):
            errors.append(f"{slide_id} requires sources but lacks source_ids or claim_ids")
        if row["role"] in {"factual", "map", "relationship", "timeline", "comparison"} and row["requires_sources"] is not True:
            errors.append(f"{slide_id} role {row['role']} must set requires_sources to true")
        for source_id in source_ids:
            if source_id not in sources:
                errors.append(f"{slide_id} references unknown source {source_id}")
        required_claim_sources: set[str] = set()
        for claim_id in claim_ids:
            claim = claims.get(claim_id)
            if not claim:
                errors.append(f"{slide_id} references unknown claim {claim_id}")
                continue
            required_claim_sources.update(claim.get("source_ids", []))
            allowed_slides = claim.get("allowed_slides", [])
            if allowed_slides and order not in allowed_slides:
                errors.append(f"{slide_id} uses {claim_id} outside allowed_slides")
        missing_sources = sorted(required_claim_sources - set(source_ids))
        if missing_sources:
            errors.append(f"{slide_id} omits claim sources: {', '.join(missing_sources)}")

        if not isinstance(row["prototype"], bool):
            errors.append(f"{slide_id} prototype must be boolean")
        style_reference_ids = row["style_reference_ids"] if is_string_list(row["style_reference_ids"]) else []
        if not is_string_list(row["style_reference_ids"]):
            errors.append(f"{slide_id} style_reference_ids must contain only non-empty strings")
        elif row["prototype"] is True and style_reference_ids:
            errors.append(f"{slide_id} is a prototype and should not reference another prototype")
        elif row["prototype"] is False and not style_reference_ids:
            errors.append(f"{slide_id} must reference at least one approved style prototype")
        for reference_id in style_reference_ids:
            if reference_id not in prototype_ids:
                errors.append(f"{slide_id} references non-prototype style anchor {reference_id}")
            if reference_id == slide_id:
                errors.append(f"{slide_id} cannot reference itself as a style anchor")

        route = row["model_route"]
        if not isinstance(route, str) or route not in ALLOWED_ROUTES:
            errors.append(f"{slide_id} has forbidden model route: {route}")
        if route == "openai-api-gpt-image-2" and row["api_authorized"] is not True:
            errors.append(f"{slide_id} uses the API route without api_authorized=true")
        if route == "codex-built-in-gpt-image-2" and row["api_authorized"] is True:
            warnings.append(f"{slide_id} marks API authorization but uses the built-in route")
        if route == "planning-only":
            if row["api_authorized"] is not False:
                errors.append(f"{slide_id} planning-only route requires api_authorized=false")
            if row["status"] != "planned":
                errors.append(f"{slide_id} planning-only route must remain planned")
            if require_complete:
                errors.append(f"{slide_id} planning-only route cannot pass the full completion gate")
        if not isinstance(row["api_authorized"], bool):
            errors.append(f"{slide_id} api_authorized must be boolean")

        status = row["status"]
        if not isinstance(status, str) or status not in ALLOWED_STATUSES:
            errors.append(f"{slide_id} has invalid status: {status}")
        if not isinstance(row["attempts"], int) or isinstance(row["attempts"], bool) or row["attempts"] < 0:
            errors.append(f"{slide_id} attempts must be a non-negative integer")
        qa = row["qa"] if isinstance(row["qa"], dict) else {}
        if set(qa) != QA_FIELDS or any(not isinstance(qa.get(field), bool) for field in QA_FIELDS):
            errors.append(f"{slide_id} qa must contain four boolean fields: {', '.join(sorted(QA_FIELDS))}")
        if status in FINAL_STATUSES and not all(qa.get(field) is True for field in QA_FIELDS):
            errors.append(f"{slide_id} has a final status without complete QA")
        if require_complete and status not in FINAL_STATUSES:
            errors.append(f"{slide_id} is not complete: {status}")

        if not safe_relative_image(row["image"]):
            errors.append(f"{slide_id} image must be a safe path under slides/")
        elif check_files and status in {"generated"} | FINAL_STATUSES:
            image_path = manifest_path.parent / row["image"]
            slides_root = (manifest_path.parent / "slides").resolve()
            if not image_path.resolve().is_relative_to(slides_root):
                errors.append(f"{slide_id} image resolves outside slides/: {image_path}")
            else:
                inspect_image(image_path, slide_id, tolerance, errors, image_hashes, warnings)

    if require_complete:
        for claim_id in sorted(set(claims) - used_claim_ids):
            warnings.append(f"Unused claim in completed deck: {claim_id}")
        for source_id in sorted(set(sources) - used_source_ids):
            warnings.append(f"Unused source in completed deck: {source_id}")
    return prototype_ids, used_claim_ids, used_source_ids


def validate_style_contract(path: Path, prototype_ids: set[str], errors: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"Missing style contract: {path}")
        return
    if not text.strip():
        errors.append(f"Style contract is empty: {path}")
        return
    if "16:9" not in text:
        errors.append("style_contract.md must declare 16:9")
    for prototype_id in sorted(prototype_ids):
        if prototype_id not in text:
            errors.append(f"style_contract.md does not name prototype {prototype_id}")


def validate_research_brief(path: Path, errors: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"Missing research brief: {path}")
        return
    if not text.strip():
        errors.append(f"Research brief is empty: {path}")
        return
    required_markers = {
        "Question ID": "research-question coverage table",
        "Status": "coverage status column",
        "Claim IDs": "claim mapping column",
        "Source IDs": "source mapping column",
    }
    for marker, label in required_markers.items():
        if marker not in text:
            errors.append(f"research_brief.md is missing the {label}: {marker}")
    if not re.search(r"\bQ-\d{3,}\b", text):
        errors.append("research_brief.md needs at least one Q-### research question")
    if not re.search(r"\b(?:covered|contested|out-of-scope)\b", text):
        errors.append("research_brief.md needs a final coverage status")


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    ledger = load_json(args.sources, errors)
    rows = load_manifest(args.manifest, errors)
    sources, claims = validate_ledger(ledger, errors, warnings)
    style_contract = args.style_contract or args.manifest.parent / "style_contract.md"
    research_brief = args.research_brief or args.manifest.parent / "research" / "research_brief.md"
    prototype_ids: set[str] = set()
    if rows:
        prototype_ids, _, _ = validate_manifest(
            rows,
            sources,
            claims,
            args.manifest,
            args.check_files,
            args.require_complete,
            args.aspect_tolerance,
            errors,
            warnings,
        )
        validate_style_contract(style_contract, prototype_ids, errors)
        if args.require_complete or args.research_brief:
            validate_research_brief(research_brief, errors)

    report = {
        "ok": not errors,
        "slide_count": len(rows),
        "source_count": len(sources),
        "claim_count": len(claims),
        "prototype_count": len(prototype_ids),
        "style_contract": str(style_contract),
        "research_brief": str(research_brief) if args.require_complete or args.research_brief else None,
        "errors": errors,
        "warnings": warnings,
    }
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
