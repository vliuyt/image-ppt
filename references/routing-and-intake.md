# Routing and intake

## 1. Confirm the delivery format

This is a hard gate. If the user has not explicitly accepted a flattened, non-editable result, ask:

> 需要可编辑 PPTX、HTML 网页演示，还是不可编辑的逐页图片 + PDF？

Do not offer image-first as a hidden implementation detail. The choice changes editability, accessibility, file size, and revision cost.

| User need | Correct owner | Why |
|---|---|---|
| Editable text, shapes, charts, notes, or master layouts | `ppt-master` | Owns the PowerPoint lifecycle |
| Browser playback, interactive components, responsive pages, one HTML file | `guizang-ppt-skill` | Owns web presentation delivery |
| Fixed visual pages, one rendered image per slide, PDF handoff | `image-ppt` | Owns the flattened image workflow |
| Illustration, cover, background, diagram, or poster without a deck | `imagegen` | Owns standalone image work |

## 2. Intake fields

Record the following before research. Infer low-risk defaults only when the user already supplied enough context.

- Audience and assumed knowledge
- Presentation goal and setting
- Language and terminology rules
- Expected duration and slide count or range
- Whether full spoilers are allowed
- Required, forbidden, or sensitive content
- Source boundary and recency requirement
- Whether citations must appear on-slide, in notes, or only in the evidence package
- Branding or visual constraints
- Target viewing device and minimum readable text size
- Runtime mode: `codex-built-in`, `openai-api`, or `planning-only`
- Whether API generation is explicitly authorized; default is no
- Delivery folder and filename

## 3. Runtime capability gate

After the format is confirmed, verify the actual image-generation route. Read [runtime support](runtime-support.md). A full run requires Codex built-in image generation or an explicitly authorized callable `gpt-image-2` API/tool route. When neither is available, switch to `planning-only` and state the incomplete deliverables before doing research.

## 4. Research mode

Choose and record exactly one:

- `source-locked`: use only user-provided sources; state gaps rather than filling them from memory.
- `research-backed`: browse and prefer primary or authoritative sources; default for factual public-education decks.
- `editorial`: sources still support factual claims, but the narrative framing and visual metaphors are original editorial work.

If the topic is current, niche, disputed, high-stakes, or explicitly asks for citations, browse before content lock. When a named document, site, film, paper, dataset, or edition matters, obtain that exact source rather than substituting memory.

## 5. Content boundary

Write a one-paragraph boundary statement. Examples:

- “Original text only; later myth retellings are labeled and excluded from the main chronology.”
- “Publicly announced film information may appear only in a final appendix; no plot inference.”
- “Medical claims use current official guidance and do not become personal medical advice.”

The boundary statement becomes a generation invariant and a QA criterion.
