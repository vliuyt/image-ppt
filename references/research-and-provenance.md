# Research and provenance

## Research sequence

1. Convert the brief into research questions and a coverage table.
2. Gather primary or authoritative sources first. Add high-quality secondary scholarship for interpretation and contested points.
3. Separate source layers. A common taxonomy is `primary`, `later-tradition`, `scholarship`, `official-current`, and `context`.
4. Record claims at the precision they will appear on slides and label each as direct evidence, synthesis, or contested interpretation.
5. Identify contradictions, uncertainty, translation differences, date ranges, and later additions.
6. Write the research brief only from claims in the ledger.
7. Resolve every research question as `covered`, `contested`, or `out-of-scope`, then run the coverage gate before outlining slides.

## Research question coverage

The research brief must include a compact table with these columns:

- Question ID and question
- Status: `covered`, `contested`, or `out-of-scope`
- Claim IDs
- Source IDs
- What the audience needs to understand

Do not hide missing coverage inside prose. A disputed question stays `contested`; an intentionally excluded question states why it is outside the content boundary.

## Required source ledger

Create `research/source_ledger.json`:

```json
{
  "research_mode": "research-backed",
  "content_boundary": "Original source material is primary; later tradition is labeled.",
  "sources": [
    {
      "id": "SRC-001",
      "title": "Source title",
      "kind": "primary",
      "creator": "Author or institution",
      "edition_or_date": "Edition, publication date, or n.d.",
      "location": "https://example.org/source or a workspace-relative path",
      "accessed": "YYYY-MM-DD",
      "notes": "Scope and reliability notes"
    }
  ],
  "claims": [
    {
      "id": "CLM-001",
      "text": "The exact proposition that may appear in the deck.",
      "source_ids": ["SRC-001"],
      "confidence": "high",
      "source_layer": "primary",
      "support_type": "direct",
      "caveat": "Any uncertainty or competing interpretation",
      "allowed_slides": [1, 2]
    }
  ]
}
```

Use stable IDs. Do not cite search-result pages. Keep quotes short and within copyright limits; prefer accurate paraphrase. When translations differ, identify the edition or translation used.

Source-quality requirements:

- A `primary` source records its edition, translation, or date.
- An `official-current` web source records its access date.
- A `synthesis` claim uses more than one source when the conclusion combines evidence.
- A `contested` claim has a non-empty caveat that names the uncertainty or competing interpretation.
- `medium` and `low` confidence claims have a caveat; reduce or omit the claim when the uncertainty cannot be explained clearly on the slide.

## Research brief

Create `research/research_brief.md` with:

- Content boundary and research mode
- Five to twelve essential takeaways
- Chronology or causal chain
- Key people, concepts, places, and relationships
- Disputed or uncertain points
- Research-question coverage table
- Source conflicts and how the deck will represent them
- Source-layer distinctions the audience must understand
- Common misconceptions to avoid
- Slide-worthy maps, diagrams, timelines, or comparisons
- Gaps that remain unresolved

## Coverage gate

Research is locked only when:

- Every factual statement intended for the deck maps to at least one claim ID.
- Every claim maps to one or more real sources.
- Every research question has an explicit final status.
- Uncertainty and disagreement are visible rather than flattened into certainty.
- Source layers are not blended without labels.
- Direct evidence, synthesis, and contested interpretation are distinguishable.
- The deck can be outlined without adding facts from memory.

If the gate fails, continue research or reduce the claim. Do not start image generation.
