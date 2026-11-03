#!/usr/bin/env python3
"""Check required files, Skill metadata, and the local SVG icon library."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "SKILL.md", "README.md", "LICENSE", "NOTICE", "VERSION.json",
    "requirements.txt", "requirements-image-analysis.txt", "run_workflow.py",
    "core/ppt_builder.py", "core/image_analyzer.py", "core/structure_analyzer.py",
    "schemas/page_spec.schema.json", "assets/icon_library/INDEX/icon_manifest.json",
    ".github/workflows/tests.yml",
]


def main() -> int:
    missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
    if missing:
        print("Missing required files:", *missing, sep="\n- ")
        return 2

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\s*\n(.*?)\n---\s*\n", skill, re.S)
    if not frontmatter:
        print("SKILL.md is missing YAML frontmatter")
        return 2
    if not re.search(r"(?m)^name:\s*ppt-reconstruction\s*$", frontmatter.group(1)):
        print("SKILL.md name must be ppt-reconstruction")
        return 2
    if not re.search(r"(?m)^description:\s*.+$", frontmatter.group(1)):
        print("SKILL.md description is required")
        return 2

    version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "assets/icon_library/INDEX/icon_manifest.json").read_text(encoding="utf-8"))
    svg_count = len(list((ROOT / "assets/icon_library/SVG").rglob("*.svg")))
    if len(manifest) != 500 or svg_count != 500:
        print(f"Icon library mismatch: manifest={len(manifest)}, SVG files={svg_count}")
        return 2

    print(f"Release verification PASS | package={version.get('package_version')} | workflow={version.get('workflow_version')} | SVG icons={svg_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
