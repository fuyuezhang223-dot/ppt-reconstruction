---
name: ppt-reconstruction
description: Reconstruct reference slide images into high-fidelity, editable PowerPoint presentations. Use when a user wants to convert slide screenshots or images into PPTX with native text, shapes, connectors, tables, charts, and reviewed SVG icon suggestions.
compatibility: Requires Python 3.10+ and local access to this repository. OCR and visual-structure analysis require optional dependencies; LibreOffice is optional for automatic preview rendering.
metadata:
  version: "1.0.0"
  workflow-version: "4.4.1"
  language: "zh-CN"
---

# PPT Reconstruction Skill

Use the repository's existing Python engine. Do not rewrite the PPT generation logic in a conversation when the scripts are available.

## First-time setup

1. Read `README.md` and `00_开始使用.md`.
2. Read `02_工作流执行规范.md` and `03_图标与素材规范.md`; these are the authoritative operational rules.
3. Keep the repository directory structure intact. Run commands from the repository root.
4. Install base dependencies with `python -m pip install -r requirements.txt`.
5. For local OCR and image-structure analysis, install `python -m pip install -r requirements-image-analysis.txt`.

## Task workflow

### A. Analyze reference images

Run:

```bash
python run_workflow.py analyze-image --input <image-or-folder> --output-dir outputs/<job-name> --build-draft
```

Review `overlay_*.png`, `analysis_*.json`, `image_analysis_report.json`, and `draft_spec.json`. Treat all OCR, geometry, arrow, table, icon, and repeated-layout outputs as candidates requiring human review. The generated `draft.pptx` is a first-pass editable draft, not a finished reconstruction.

### B. Build an editable deck

Create or revise a `page_spec` JSON file using `schemas/page_spec.schema.json`. Prefer the existing components in `core/component_registry.py`; use native PowerPoint objects when a component does not fit. Preserve stable element IDs and normalized bounding boxes.

Run:

```bash
python run_workflow.py build --spec <page-spec.json> --output outputs/<name>.pptx --compare
```

### C. Quality assurance and repair

Run:

```bash
python run_workflow.py qa outputs/<name>.pptx
```

When a trusted reference image and verified coordinates exist, use `compare` and the restricted `repair` command. Never set `source_ref.verified=true` without human verification. Re-run build and QA after any repair.

### D. Icon policy

Use `python run_workflow.py search-icon "<Chinese keyword>"` and inspect the returned SVG before selecting its `icon_id`. Standard icons must come from `assets/icon_library/SVG`; do not crop icons from slide screenshots. Icon suggestions from image analysis are contextual search candidates, not pixel-level recognition. The current PPT builder rasterizes SVG icons to PNG objects; do not describe them as path-editable vector icons.

## Required delivery

Provide:

- editable `.pptx`;
- source `page_spec` JSON;
- preview images when rendering is available;
- machine QA report and visual comparison artifacts where applicable;
- icon IDs and asset provenance;
- unresolved OCR or structural items requiring human review.

## Hard limits

- Never use a full-slide screenshot as a substitute for an editable slide.
- Never invent unreadable text, data, arrow direction, or business relationships.
- Never claim pixel-perfect or 100% fidelity from machine QA alone.
- Distinguish native editable objects from independent raster image objects.
- If local scripts or assets are inaccessible in the current environment, say so and do not pretend they were executed.
