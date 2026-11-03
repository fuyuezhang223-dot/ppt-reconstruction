# Architecture

## Processing pipeline

1. **Input collection** — accepts one image or a directory of images; files are sorted deterministically.
2. **Image analysis** — `core/image_analyzer.py` extracts OCR text, confidence and bounding boxes when an OCR engine is available.
3. **Structure proposals** — `core/structure_analyzer.py` detects geometric shapes, arrow candidates, table grids, compact icon regions and repeated-card layout hypotheses using OpenCV heuristics.
4. **Reviewable intermediate data** — analysis JSON, overlay images and `page_spec` drafts preserve confidence and review flags. The draft is not treated as verified semantic truth.
5. **PPTX generation** — `core/component_registry.py` expands reusable components; `core/ppt_builder.py` creates native PowerPoint objects.
6. **Quality checks** — `core/quality.py` checks file structure; `core/reference_compare.py` compares rendered slides with trusted references; `core/repair_engine.py` applies only permitted geometry repairs and regression checks.

## Main modules

| Module | Responsibility |
|---|---|
| `core/image_analyzer.py` | OCR adapter, image collection, page metadata, draft `page_spec`, review overlays |
| `core/structure_analyzer.py` | Geometry, arrow, table, icon-context and repeated-layout candidates |
| `core/component_registry.py` | Eight reusable component types and expansion to primitive elements |
| `core/ppt_builder.py` | Native PowerPoint slide and object generation |
| `core/icon_library.py` | Local 500-SVG lookup and semantic search |
| `core/quality.py` | PPTX structure checks and optional rendering |
| `core/reference_compare.py` | Reference rendering, overlays and visual-difference reports |
| `core/repair_engine.py` | Restricted geometry repairs with audit and regression checks |

## Intermediate contract

`schemas/page_spec.schema.json` is the central data contract between analysis, human/AI review and the PPTX builder. Keep coordinates normalized (`bbox_norm`) and give each element a stable ID. Schema changes should be backward-compatible where possible and accompanied by examples and tests.

## Safety and quality gates

- OCR confidence does not prove that the text is correct.
- Geometric classification does not prove the business meaning of a shape.
- Arrow candidates do not prove direction or process semantics.
- Icon suggestions are contextual semantic search results, not image classification.
- Only human-verified reference geometry may be used for automatic repair.
- Machine QA passing does not certify visual fidelity or semantic correctness.

## Runtime notes

Base PPTX generation uses Python and `python-pptx`. Image analysis additionally uses OpenCV and optionally RapidOCR or Tesseract. Preview rendering uses LibreOffice when available. All output is local in the current version.
