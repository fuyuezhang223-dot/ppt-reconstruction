# Product roadmap

This repository is the first public-facing package: an Agent Skill plus a local Python CLI. It is not yet a hosted SaaS or a complete desktop application.

## Phase 1 — Public Skill + CLI

- Standard Agent Skill entry point and usage instructions.
- Reusable PPTX builder, schemas, component registry and local icon library.
- Local image analysis, review overlays, QA and constrained repair.
- CI regression tests and reproducible demo commands.

## Phase 2 — Local visual workbench

- Add a small local web UI for batch upload, page thumbnails, OCR correction, element selection and preview.
- Allow users to accept/reject geometry and arrow candidates before building.
- Show editable-object counts and raster-image counts per slide.
- Preserve the same `page_spec` contract and Python builder.

## Phase 3 — Hosted service or desktop app

- Add job queue, progress reporting, retry and cancellation.
- Add user-controlled storage, retention and deletion.
- Add model-provider configuration and transparent API-cost controls.
- Add authentication, usage limits, billing and monitoring only after quality and demand are validated.

## Release gates before Phase 2

- Benchmark at least 20–30 diverse reference slides.
- Track OCR character error rate, shape precision/recall, arrow direction accuracy, table cell accuracy and human correction time.
- Fix performance regressions on dense diagrams and long batch jobs.
- Verify rendering on PowerPoint and WPS in addition to LibreOffice.
- Document the difference between native editable objects and image-backed objects.
