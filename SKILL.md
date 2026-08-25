---
name: image-ppt
description: "Create research-backed, non-editable 16:9 slide images plus PDF after flattened output is confirmed. Prefer Codex built-in gpt-image-2; elsewhere require a callable gpt-image-2 tool or authorized API. Without it, deliver planning-only. Route editable PPTX to ppt-master, HTML to guizang-ppt-skill, and standalone images to imagegen. 中文触发：不可编辑图片版PPT、逐页图片合成PDF、图片型演示。"
---

# Image-PPT

## Route gate — blocking

Use `ppt-master` for editable PPTX, `guizang-ppt-skill` for HTML, and `imagegen` for standalone images. Continue here only for confirmed full-slide images + PDF. If format is unclear, ask: “需要可编辑 PPTX、HTML 网页演示，还是不可编辑的逐页图片 + PDF？”

## Runtime gate — blocking

Read [runtime support](references/runtime-support.md). Record a verified mode: `codex-built-in`, authorized `openai-api`, or `planning-only`. A runtime name does not prove image capability. Planning-only cannot claim `final_deck.pdf`.

## Workflow

1. Read [routing and intake](references/routing-and-intake.md); lock audience, purpose, length, exclusions, research mode, and runtime mode.
2. Read [research and provenance](references/research-and-provenance.md); create the brief and source/claim ledger before outlining.
3. Read [deck contract](references/deck-contract.md); lock outline, copy, style contract, three prototypes, and manifest.
4. Planning-only: deliver prompts and handoff, then stop. Full run: read the installed image tool contract and keep all pages on `gpt-image-2`.
5. Approve the three prototypes, reuse them as style references, and resume from the manifest without regenerating valid pages.
6. Read [generation and QA](references/generation-and-qa.md); inspect and repair every page, then run the [validator](scripts/validate_deck.py), [contact sheet](scripts/build_contact_sheet.py), and [PDF assembler](scripts/assemble_pdf.py).

## Non-negotiable contracts

- Order: research → claims → outline → images.
- Map factual slides to claim/source IDs and preserve source-layer labels.
- Verify every visible character, name, numeral, and page number.
- Never change provider/model silently. API use requires explicit approval.
- Record any `gpt-image-2` background + deterministic-typesetting fallback; never change facts to pass generation.
- Re-run [trigger evals](evals/trigger_cases.json) after boundary changes.

## Completion gate

- Full: aligned research, outline, style, manifest, slides, contact sheet, `final_deck.pdf`, and QA report; verify count, order, 16:9, text, facts, and style.
- Planning-only: research, outline, style, manifest, exact prompts, and `handoff.md`; explicitly mark images and PDF incomplete.

Public brand asset: [hero banner](assets/hero.png).
