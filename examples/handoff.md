# Planning-only handoff

- Runtime mode: `planning-only`
- Capability check: no callable `gpt-image-2` image-generation route was available.
- Prepared: research brief, source ledger, outline, style contract, manifest, and exact per-slide prompts.
- Incomplete: slide images, contact sheet, visual QA, and `final_deck.pdf`.
- Resume rule: switch each manifest row to `codex-built-in-gpt-image-2` or an explicitly authorized `openai-api-gpt-image-2` route, generate the three prototypes, then continue through visual QA and PDF assembly.

Do not report the presentation as complete until every page reaches `validated` or `fallback-typeset` and the PDF page count has been verified.
