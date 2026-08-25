# Runtime support

## Capability rule

Image-PPT is an Agent Skill with one hard requirement for a finished deck: the host must expose a callable image-generation route that actually uses `gpt-image-2`.

Do not equate “Agent Skills compatible” with “can generate images.” Agent Skills compatibility covers discovery and instruction loading; image generation is a separate host capability.

## Support matrix

| Runtime | Support level | Required condition |
|---|---|---|
| Codex with built-in image generation | Full, preferred | Built-in image generation is available in the current session and uses `gpt-image-2` |
| Codex using the OpenAI API route | Full, conditional | User explicitly approves API billing; credentials stay local; the callable route uses `gpt-image-2` |
| Other Agent Skills runtime | Full, conditional | The host exposes a callable `gpt-image-2` image tool, can save one image per slide, and can run the local QA/PDF scripts |
| Runtime without compatible image generation | Planning only | Produce research, outline, style system, manifest, and prompts; stop before image and PDF completion |

## Capability check

Before research or generation, record one runtime mode:

- `codex-built-in`: confirm the built-in image-generation tool is callable. Do not request an API key.
- `openai-api`: confirm the user explicitly authorized this separately billed route and that the environment can call the OpenAI Images API with `gpt-image-2`. Never request a secret in chat.
- `planning-only`: use when neither route is available or authorized.

A model name in a configuration file is not proof that the image endpoint works. Do not treat chat-completions access, image input, or a generic multimodal model as image-generation capability.

## Planning-only handoff

Use `model_route: planning-only`, `api_authorized: false`, and `status: planned` in every manifest row. Deliver:

- `research/research_brief.md`
- `research/source_ledger.json`
- `deck_outline.md`
- `style_contract.md`
- `deck_manifest.jsonl`
- exact per-slide prompts
- `handoff.md` naming the missing capability and the two supported continuation routes

Do not create placeholder slide files, a fake contact sheet, or an empty PDF. Do not describe the deck as generated, validated, or complete.

## Full-run handoff from another runtime

If another runtime creates the images, preserve stable filenames under `slides/`, record the actual route in every manifest row, and run the same validator, contact sheet, per-page visual review, and PDF assembly gates. Structural Agent Skills compatibility alone does not waive these checks.
