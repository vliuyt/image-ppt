# Release validation

Release candidate: 0.3.0

Date: 2026-08-25

| Gate | Result |
|---|---|
| Skill validation, lint, governance, resource boundary | Pass; no warnings |
| Initial-load budget | 1,012 / 1,300 estimated tokens |
| Trigger routing | 23 / 23 cases passed; 0 false positives; 0 false negatives |
| Output contract fixtures | 7 / 7 with-Skill cases passed; 0 regressions |
| Trust scan | 20 files; 0 secret findings; 0 failures; 0 warnings |
| Skill IR compiler | 5 / 5 targets passed |
| Runtime conformance | 5 / 5 targets passed |
| Package verification | 4 adapters, 57 safe archive entries, 0 failures, 0 warnings |
| Temporary install simulation | Pass; 4 permission contracts enforced |
| Repository unit tests | 5 / 5 passed |
| Review Studio | 0 blockers; optional enhanced evidence remains unclaimed |
| Hero image | 1,672 × 941; 16:9 visual inspection passed |

Raw machine reports contain workstation paths, so they are excluded from the public repository. This file preserves the release summary without personal paths or private deck content.

## Online validation

| Check | Result |
|---|---|
| Public repository | `vliuyt/image-ppt`, visibility PUBLIC |
| Default branch | `main` |
| Release | `v0.3.0` published |
| Main GitHub Actions run | Success |
| Installer discovery | `npx skills add vliuyt/image-ppt --list` found exactly one Skill: `image-ppt` |
| Maintenance automation | Monthly CI and Dependabot active; initial update PRs created |
