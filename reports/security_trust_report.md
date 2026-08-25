# Security and trust report

Release candidate: 0.3.0

Review date: 2026-08-25

- No bundled credentials or private keys are permitted.
- API use requires explicit user approval; credentials remain in the host's local environment.
- Manifest image paths are restricted to the deck's `slides/` directory.
- Contact-sheet and PDF outputs require explicit overwrite flags when a target already exists.
- Remote inline execution is forbidden by the interface contract.
- Public-release checks scan text files for common secrets and personal absolute paths.

Final trust scan: 20 files scanned, 0 secret findings, 0 failures, and 0 warnings. See `release_validation.md` for the complete public-safe summary.
