# Contributing

Thanks for helping improve PPT Reconstruction Skill.

## Before opening an issue or pull request

- Search existing issues to avoid duplicates.
- Describe the input slide/image type and the expected output.
- Remove confidential information from sample files.
- Do not add assets unless their redistribution rights are clear.

## Development setup

```bash
python -m pip install -r requirements.txt
python -m pip install opencv-python-headless
python -m unittest discover -s tests -p "test_*.py" -v
python -m tests.smoke_test
```

OCR is optional for most tests. Use `requirements-image-analysis.txt` only when testing OCR adapters.

## Pull request expectations

- Keep OCR and structure recognition outputs explicitly reviewable.
- Never turn uncertain text, arrow directions, or icon suggestions into unverified facts.
- Add a focused regression test for every bug fix.
- Preserve stable `page_spec` fields unless a schema migration is documented.
- Keep the standard icon policy: use the SVG library; do not crop slide screenshots into icons.
- Update `CHANGELOG.md`, relevant docs and `VERSION.json` when behavior changes.
- Run the complete test suite and smoke test before requesting review.

## Code style

- Python 3.10+.
- Prefer small, deterministic functions and bounded algorithms.
- Keep file paths relative to the repository root where possible.
- Explain any heuristic threshold and preserve a human-review flag for uncertain detections.
