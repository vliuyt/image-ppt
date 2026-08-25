# Conformance matrix

Validated: 2026-08-25. All five structural targets passed the conformance suite after Skill IR compilation.

| Target | Package structure | Full image generation |
|---|---|---|
| OpenAI / Codex | Supported | Preferred with built-in `gpt-image-2`; conditional with authorized API |
| Agent Skills compatible | Supported | Conditional on a callable `gpt-image-2` tool |
| Claude adapter | Supported | Planning-only unless the host exposes that tool |
| Generic adapter | Supported | Planning-only unless the host exposes that tool |
| VS Code adapter | Supported | Planning-only unless the host exposes that tool |

Structural conformance must not be presented as proof that a host can generate images.
