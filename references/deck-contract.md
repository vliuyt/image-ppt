# Deck contract

## Slide architecture

Create `deck_outline.md`. Start with a one-sentence promise to the audience, then define the narrative arc. Each slide must have one main job.

For every slide record:

- `P01`-style ID and order
- Title
- Slide role: `cover`, `section`, `factual`, `narrative`, `map`, `relationship`, `timeline`, `comparison`, `summary`, or `sources`
- One-sentence takeaway
- Exact visible text
- Claim IDs and source IDs
- Visual composition and information hierarchy
- Speaker emphasis or narration notes
- Transition from the previous slide

Do not turn prose paragraphs into tiny slide text. Split a page when the hierarchy cannot remain readable at presentation distance.

## Visual system

Create `style_contract.md` before prompting any page:

- Art direction and historical or subject boundaries
- Aspect ratio: landscape 16:9
- Palette and contrast rules
- Typography character: family category, weight, alignment, and minimum apparent size
- Grid, margins, title zone, body zone, footer, and page-number position
- Illustration, map, diagram, portrait, and icon treatment
- Repeated navigation elements
- Prohibited elements: logos, unrequested text, anachronisms, watermarks, decorative clutter
- Approved prototype slide IDs and why each is authoritative
- Rules that may vary by page role and rules that must never drift

Generate three prototypes: cover, densest factual page, and a narrative or diagram page. They test the system better than three similar pages. Mark them `prototype: true`; every other slide must reference one or more approved prototype IDs.

## Manifest

Create `deck_manifest.jsonl`, one JSON object per line and one line per slide:

```json
{"slide_id":"P01","order":1,"title":"Title","role":"cover","takeaway":"Audience promise","visible_text":["Exact title","Exact subtitle"],"requires_sources":false,"claim_ids":[],"source_ids":[],"prototype":true,"style_reference_ids":[],"prompt":"Complete image prompt","model_route":"codex-built-in-gpt-image-2","api_authorized":false,"status":"planned","image":"slides/p01.png","attempts":0,"qa":{"text":false,"factual":false,"visual":false,"style":false},"notes":""}
```

Allowed status values:

- `planned`
- `generated`
- `validated`
- `failed`
- `fallback-typeset`

Use `codex-built-in-gpt-image-2` by default. `openai-api-gpt-image-2` is allowed only when the user explicitly approves API generation; record `api_authorized: true`. `planning-only` is valid only for an incomplete handoff and must remain `status: planned`. No other model or provider is valid.

## Prompt contract

Each slide prompt includes:

1. Purpose and audience
2. “Full 16:9 landscape presentation slide”
3. Slide role and composition
4. Shared style contract and the relevant prototype slide IDs
5. Exact visible Chinese or other copy in quotation marks
6. Subject details, relationships, spatial positions, and historical or technical constraints
7. Page number and its exact position when used
8. “No other text, no logos, no watermark”
9. Any page-specific negative constraints

Keep copy concise even though `gpt-image-2` handles Chinese. A production deck still requires word-by-word inspection.

## Content lock

Before generation, confirm:

- The outline includes the promised topic coverage.
- Every factual page contains resolvable claim and source IDs.
- Exact visible text is final enough to render.
- The visual system is consistent but permits page-type variation.
- Three representative prototypes are approved or self-checked and recorded in `style_contract.md`.
- Every non-prototype slide references an approved prototype.
- Slide count and order are locked.

After lock, content changes update the ledger, outline, and manifest together.
