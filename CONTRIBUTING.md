# Contributing

Thanks for improving Image-PPT.

## Before opening a pull request

1. Keep the Skill focused on non-editable full-slide images plus PDF.
2. Preserve the capability gate: full generation requires a callable `gpt-image-2` route.
3. Add or update trigger cases when changing routing language.
4. Add an output-eval fixture when changing a material behavior contract.
5. Run:

```bash
python scripts/check_public_release.py
python -m unittest discover -s tests -v
```

## Pull requests

Describe the user-facing problem, the smallest change that solves it, and the validation evidence. Avoid unrelated refactors. Do not commit API keys, generated private decks, personal file paths, or third-party copyrighted assets.

By contributing, you agree that your contribution is licensed under the MIT License.
