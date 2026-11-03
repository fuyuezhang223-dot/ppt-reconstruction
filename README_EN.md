# PPT Reconstruction Skill

An Agent Skill and Python CLI for rebuilding slide screenshots into editable PowerPoint decks.

The repository includes a native PPTX builder, reusable slide components, 500 Tabler SVG icons with Chinese semantic indexes, optional OCR and OpenCV structure proposals, QA, reference comparison, constrained repair, examples, and tests.

**Important:** this is not a one-click, pixel-perfect screenshot converter. OCR and visual-structure outputs are reviewable candidates. Human verification is required before delivery.

## Quick start

1. Download and extract the repository while preserving its folder structure.
2. Install Python 3.10+.
3. Run `python -m pip install -r requirements.txt`.
4. Build a demo:

```bash
python run_workflow.py build --spec examples/v42_component_demo.json --output outputs/demo.pptx
```

5. Run tests:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m tests.smoke_test
```

Optional OCR text extraction (OpenCV-based structure proposals are included in the base install):

```bash
python -m pip install -r requirements-image-analysis.txt
python run_workflow.py analyze-image --input ./slide-images --output-dir outputs/analysis --build-draft
```

See `SKILL.md` for the Agent Skill instructions and `README.md` for the full Chinese documentation.
