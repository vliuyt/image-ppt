<p align="center">
  <img src="assets/hero.png" alt="Image-PPT — Research to Slides to PDF" width="100%">
</p>

<h1 align="center">Image-PPT</h1>

<p align="center">
  A research-first Agent Skill for turning sourced content into consistent 16:9 slide images and a verified PDF with <code>gpt-image-2</code>.
</p>

<p align="center">
  <a href="https://github.com/vliuyt/image-ppt/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/vliuyt/image-ppt/actions/workflows/ci.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-0b7285.svg"></a>
  <img alt="Model" src="https://img.shields.io/badge/model-gpt--image--2-7c3aed.svg">
  <img alt="Output" src="https://img.shields.io/badge/output-16%3A9%20images%20%2B%20PDF-e67e22.svg">
</p>

<p align="center"><a href="README.zh-CN.md">简体中文</a> · English</p>

Image-PPT is for presentations whose final pages may be flattened and non-editable. It keeps research, claims, slide copy, image prompts, generation state, visual QA, and PDF assembly in one auditable workflow.

## Why it exists

Image models can produce striking individual slides, yet a real deck also needs factual provenance, consistent art direction, exact visible text, correct page order, and honest completion claims. Image-PPT adds those missing controls:

- research questions, source layers, claim IDs, and explicit content boundaries;
- a locked deck outline, exact copy, and three representative style prototypes;
- resumable generation through a JSONL manifest;
- per-slide checks plus a deck-wide contact sheet;
- PDF assembly only after every page passes the completion gate.

## Runtime support

Agent Skills compatibility describes package structure. Full slide generation additionally requires a callable `gpt-image-2` image route.

| Environment | Mode | What Image-PPT can deliver |
|---|---|---|
| Codex with built-in image generation | Full, preferred | Research → images → QA → PDF; no API key needed |
| Any agent runtime with a callable `gpt-image-2` tool | Full, conditional | Same workflow, subject to the host tool contract |
| OpenAI API route explicitly approved by the user | Full, conditional | Same workflow; credentials remain local and API usage may be billed |
| No compatible image-generation route | Planning-only | Research, source ledger, outline, copy, style contract, manifest, prompts, and handoff |

Planning-only mode never claims that slide images or `final_deck.pdf` exist.

## Install

### Codex

```bash
npx skills add vliuyt/image-ppt --agent codex --global --yes --copy
```

Restart the Codex session, then invoke the Skill explicitly:

```text
$image-ppt Create a research-backed, non-editable 16:9 image presentation and an ordered PDF about [topic].
```

### Other Agent Skills runtimes

```bash
npx skills add vliuyt/image-ppt --global --all --yes --copy
```

Installing the package does not add an image model to the host. Confirm that the current session exposes a callable `gpt-image-2` route; otherwise use the planning-only handoff.

## Workflow

```text
Format gate → Runtime gate → Research ledger → Deck contract
            → 3 style prototypes → Slide generation → Visual QA → PDF verification
```

1. Confirm the requested output is full-slide images plus PDF.
2. Verify `codex-built-in`, authorized `openai-api`, or `planning-only` mode.
3. Research the topic and map factual claims to sources before writing the deck.
4. Lock exact copy, art direction, prototypes, and the page manifest.
5. Generate and repair pages without silently changing model or provider.
6. Validate 16:9 files, text, facts, style, order, and final PDF page count.

See [SKILL.md](SKILL.md) for the entry contract and [runtime-support.md](references/runtime-support.md) for the capability boundary.

## Output contract

A full run produces:

```text
research/research_brief.md
research/source_ledger.json
deck_outline.md
style_contract.md
deck_manifest.jsonl
slides/*.png
contact_sheet.png
qa_report.md
final_deck.pdf
```

A planning-only run ends with `handoff.md` and keeps every manifest page at `status: planned`.

## Clear routing boundaries

- Editable PowerPoint: use `ppt-master`.
- HTML/browser presentation: use `guizang-ppt-skill`.
- One or a few standalone images: use `imagegen`.
- Existing PPTX-to-PDF conversion: use a document conversion tool.

## Local validation

```bash
python scripts/check_public_release.py
python -m unittest discover -s tests -v
python scripts/validate_deck.py \
  --manifest examples/planning_only_manifest.jsonl \
  --sources examples/source_ledger.json \
  --style-contract examples/style_contract.md
```

The repository also runs these checks on pull requests, pushes, manual dispatch, and a monthly schedule.

## Source and model guidance

- [OpenAI: Image generation in Codex](https://learn.chatgpt.com/docs/image-generation)
- [OpenAI: GPT Image 2 model](https://developers.openai.com/api/docs/models/gpt-image-2)

Image-PPT is an independent open-source project and is not affiliated with or endorsed by OpenAI. Generated text and factual visuals still require human review. API usage, when selected, follows the user's OpenAI account pricing and limits.

## Contributing and maintenance

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the [project roadmap](https://github.com/vliuyt/image-ppt/issues). Releases follow [CHANGELOG.md](CHANGELOG.md); dependency updates and contract tests run monthly.

## License

[MIT](LICENSE)
