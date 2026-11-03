# Changelog

## 1.0.0 — GitHub-ready package / workflow 4.4.1

- Added standard Agent Skill metadata to the root `SKILL.md`.
- Added GitHub-oriented README, English overview, contribution/security guidance, license notice and CI workflow.
- Added Windows and macOS/Linux setup helpers.
- Moved OpenCV into base requirements because the v4.4 structure-analysis tests and features depend on it; kept OCR engines optional.
- Fixed ZIP Unicode filename portability: release archives are now generated with UTF-8 filename flags.
- Fixed missing EAM icon paths caused by incorrectly decoded Chinese directory names during archive extraction.
- Replaced quadratic open-V arrow segment pairing with spatial-hash candidate pairing and nearby-shaft indexing.
- Enforced the configured maximum connector-candidate count.
- Added open-V arrow regression and dense real-slide candidate-limit tests.
- Preserved the v4.4 image-analysis and PPTX generation capabilities and their human-review boundaries.
