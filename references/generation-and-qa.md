# Generation, recovery, and QA

## Generation route

Read the installed image-generation Skill or tool contract before generating. The preferred route is Codex built-in image generation, which uses `gpt-image-2`. Generate one distinct slide per tool call. Copy each result into the project `slides/` folder using its stable manifest filename.

After the three prototypes pass QA, use the relevant approved prototype as visual guidance whenever the image tool can accept a reference image. State which composition, palette, typography character, illustration treatment, and footer rules must remain fixed. The prompt still carries the full style contract so a missing reference image does not erase the invariant.

If the user asks for large-batch API generation, explain that it is separately billed and requires explicit approval. Keep credentials local and the model at `gpt-image-2`; do not silently fall back to another endpoint or provider. If no callable image route is available, return to the planning-only handoff instead of improvising an unsupported provider.

## Resumability

- Start from the first manifest row whose status is not `validated` or `fallback-typeset`.
- Do not regenerate an existing valid image.
- Increment `attempts` and record the failure reason.
- A prompt revision changes only the affected manifest row unless the shared style contract changes.
- If the shared style changes, mark every unreviewed page for re-check; do not assume consistency.
- If an approved prototype changes, re-check every slide that lists it in `style_reference_ids`.

## Page-level QA

Open and inspect every generated slide. Check:

- `text`: every visible character, numeral, name, label, and page number matches the manifest; no extra text.
- `factual`: content matches the claim ledger and does not cross the content boundary.
- `visual`: hierarchy, legibility, contrast, crop, alignment, and meaningful visual support.
- `style`: palette, type character, illustration treatment, grid, footer, and page numbering remain coherent.

Set each manifest `qa` field to `true` only after inspection. File existence is not visual QA.

## Deck-level QA

Build a contact sheet and inspect:

- Narrative rhythm and page-type variety
- Style continuity without monotonous repetition
- Sudden typography, palette, framing, or character drift
- Duplicate or missing pages
- Dense pages that become unreadable at thumbnail scale

Then run `scripts/validate_deck.py --check-files --require-complete`. The validator also checks the research-question coverage table, style contract, prototype coverage, source layers, and source/claim references.

## Failure recovery

Use the narrowest repair:

1. Text typo or unwanted extra text: regenerate the page with exact copy and explicit “no other text.”
2. Persistent production-critical text issue: generate a text-free `gpt-image-2` background with reserved copy zones, then add exact text locally. Mark the status `fallback-typeset` and record the method.
3. Safety false positive: preserve the factual content. Reframe the image request toward a neutral scene or background, then typeset the exact content locally. Do not euphemize, omit, or distort facts merely to pass generation.
4. Style drift: attach a representative approved page as visual guidance and specify what must remain fixed.
5. Wrong route or provider: stop, restore `gpt-image-2`, and report the route mismatch. Do not conceal substitution.

## PDF and delivery QA

Assemble only pages with status `validated` or `fallback-typeset`. Verify:

- Manifest rows, image files, and PDF pages have the same count and order.
- Every slide is within the 16:9 tolerance.
- The PDF opens and renders.
- First, middle, last, and all fallback pages render correctly.
- `contact_sheet.png` matches the final manifest after all repairs.
- `qa_report.md` lists evidence, repaired pages, fallbacks, unresolved caveats, and the final page count.

Deliver the outline, source ledger, manifest, image folder, PDF, and QA report together. The PDF alone is insufficient for an auditable workflow.
