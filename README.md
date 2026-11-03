# PPT Reconstruction Skill

**High-fidelity image-to-editable-PowerPoint reconstruction toolkit**  
**GitHub package:** `1.0.0` · **Workflow engine:** `4.4.1` · **Language:** Chinese-first, English-friendly

将 PPT 页面截图重建为可编辑 PowerPoint 的 AI Skill + Python CLI 项目。仓库包含可复用的 PPTX 生成引擎、8 类页面组件、500 个 Tabler SVG 图标及中文索引、图片 OCR/结构候选分析、视觉 QA、受限修复、示例和测试。

> **能力边界：** 本项目不是“任意截图一键 100% 复刻”。OCR、几何、箭头、表格、图标和重复布局分析输出的是待复核候选。正式交付前仍需人工检查文字、业务关系、图标语义和视觉效果。

## What it does

- Builds editable PPTX files from structured `page_spec` JSON.
- Provides reusable native PowerPoint components: text, shapes, connectors, tables, charts, cards and layouts.
- Analyzes slide images with optional OCR and OpenCV-based geometry/arrow/table/icon-context proposals.
- Searches a local library of 500 Tabler SVG icons with Chinese semantic indexes.
- Produces QA reports, preview renders, reference overlays and constrained geometry repairs.

## Quick start (Windows)

1. Download the repository ZIP and extract it. **Keep the directory structure intact.**
2. Install Python 3.10 or later.
3. Open PowerShell in the repository root and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup.ps1
```

4. Build the included demo:

```powershell
.\.venv\Scripts\python.exe run_workflow.py build --spec examples/v42_component_demo.json --output outputs/v42_demo.pptx
```

5. Run tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -m tests.smoke_test
```

OpenCV is included in the base install for geometry, arrow and table proposals. To add OCR text extraction:

```powershell
.\scripts\setup.ps1 -WithImageAnalysis
```

This installs RapidOCR and the Tesseract Python wrapper. Tesseract fallback additionally requires the Tesseract executable and language data (`chi_sim` / `eng`). LibreOffice is optional and is used for automatic preview rendering.

## Analyze images and build a draft

```powershell
python run_workflow.py analyze-image --input "D:\PPT图片\一组截图" --output-dir outputs\batch01 --build-draft
```

Review the generated overlay images, OCR results, structure candidates and `draft_spec.json`. The draft is a starting point for human correction, not a final slide deck.

## Build from a page specification

```powershell
python run_workflow.py build --spec examples/v42_component_demo.json --output outputs/demo.pptx --compare
python run_workflow.py qa outputs/demo.pptx
```

Search the icon library:

```powershell
python run_workflow.py search-icon "维护"
```

## Use as an Agent Skill

This repository is itself a Skill folder because it contains a root-level `SKILL.md` with Agent Skills metadata. In a compatible Agent Skills client, add or copy this folder into that client's supported skills directory. The client must also be able to access the repository files and execute the Python commands. Skill loading does not install Python dependencies automatically.

The skill instructions are in [`SKILL.md`](SKILL.md). For operational details, read:

- [`00_开始使用.md`](00_开始使用.md)
- [`02_工作流执行规范.md`](02_工作流执行规范.md)
- [`03_图标与素材规范.md`](03_图标与素材规范.md)
- [`04_验收与适用边界.md`](04_验收与适用边界.md)

## Architecture

```text
Reference images
      │
      ▼
OCR + OpenCV structure proposals
      │  (all proposals require review)
      ▼
page_spec JSON  ◄── human / vision-model correction
      │
      ▼
Native PPTX builder + component registry + SVG icon library
      │
      ▼
QA / reference comparison / restricted repair
      │
      ▼
Editable PPTX + preview + JSON + QA report
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for module boundaries and [`docs/PRODUCT_ROADMAP.md`](docs/PRODUCT_ROADMAP.md) for the planned desktop/web product path.

## Repository layout

```text
SKILL.md                 Agent Skill entry point
run_workflow.py          CLI entry point
core/                    PPT builder, image analyzer, structure analyzer, QA, repair
assets/icon_library/     500 SVG icons, indexes, and upstream license
config/                  Design tokens, QA thresholds, repair policy
schemas/                 page_spec JSON Schema
examples/                synthetic demos and six-page EAM reference case
tests/                   unit, regression, and smoke tests
scripts/                 setup and release helper scripts
docs/                    architecture and product notes
```

## Tests

The repository CI runs the unit/regression suite and smoke test on Python 3.10–3.12. OpenCV is part of the base dependencies; OCR engines are optional and are not required for the test suite.

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m tests.smoke_test
```

Latest local verification for this package: **35 unit tests passed**, smoke test passed, and the dense EAM slide arrow-candidate test completed in about 2.2 seconds in the current test environment. This is a regression result, not a universal runtime guarantee or an image-recognition accuracy benchmark.

## Licensing

- Original workflow code and documentation: MIT License, see [`LICENSE`](LICENSE).
- The 500 SVG icons are from [Tabler Icons](https://github.com/tabler/tabler-icons), under their MIT license. The upstream license is retained at [`assets/icon_library/LICENSES/TABLER_LICENSE.txt`](assets/icon_library/LICENSES/TABLER_LICENSE.txt).
- Third-party fonts, sample images, and other externally sourced materials retain their own rights and terms. Check the relevant source before redistributing modified or additional assets.

## Current limitations

- OCR quality depends on image clarity, font, language pack and OCR engine.
- Arrow, shape and table recognition are geometry-based proposals, not semantic understanding.
- Icon suggestions use nearby OCR labels to search the SVG index; they are not pixel-level icon recognition.
- SVG icons are currently rasterized to PNG when inserted into PPTX; their paths are not individually editable in PowerPoint.
- A six-page EAM case uses a dedicated page template and is not proof of arbitrary screenshot auto-reconstruction.
- The repository currently provides a local CLI and Agent Skill, **not** a hosted SaaS, account system or multi-user web application.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Please include a minimal reproducible example and tests for algorithm changes.
