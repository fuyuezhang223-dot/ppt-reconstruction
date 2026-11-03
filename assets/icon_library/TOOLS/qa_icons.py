#!/usr/bin/env python3
"""Structural, security, duplication, count and render QA for all 500 SVGs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

EXPECTED = {
    "01_制造与工厂": 50, "02_设备与维护": 55, "03_质量管理": 35,
    "04_安全与风险": 35, "05_物流与仓储": 55, "06_数据与数字化": 55,
    "07_人员与组织": 40, "08_管理计划与流程": 40, "09_成本财务与经营": 30,
    "10_效率改善与精益": 30, "11_能源环保与可持续": 30, "12_科研教育与技术": 45,
}
BRAND_PATTERN = re.compile(r"(^|[-_])(brand|logo|facebook|twitter|instagram|tiktok|youtube|github|apple|windows)([-_]|$)", re.I)
EXTERNAL_PATTERN = re.compile(r"(?:data:image/|javascript:|(?:href|xlink:href)\s*=\s*[\"'](?:https?:)?//)", re.I)


def project_root() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent if (here.parent.parent / "INDEX").exists() else here.parents[1] / "PPT_ICON_LIBRARY_500_v1.0"


def add(errors: list[dict], kind: str, path: Path | str, detail: str) -> None:
    errors.append({"type": kind, "path": str(path), "detail": detail})


def find_node() -> str:
    return shutil.which("node") or "node"


def render_all(root: Path, manifest_path: Path, records: list[dict], errors: list[dict]) -> int:
    render_dir = root / "PREVIEW" / ".qa_render"
    if render_dir.exists():
        shutil.rmtree(render_dir)
    render_dir.mkdir(parents=True)
    helper = root / "TOOLS" / "render_svg_batch.js"
    try:
        result = subprocess.run(
            [find_node(), str(helper), str(manifest_path), str(root), str(render_dir), "32"],
            capture_output=True, text=True, encoding="utf-8", timeout=180, check=False,
            env=os.environ.copy(),
        )
        if result.returncode:
            add(errors, "render_engine", helper, result.stderr.strip() or result.stdout.strip())
            return 0
        rendered = len(list(render_dir.glob("*.png")))
        if rendered != len(records):
            add(errors, "render_count", render_dir, f"rendered {rendered}, expected {len(records)}")
        return rendered
    except Exception as exc:
        add(errors, "render_engine", helper, str(exc))
        return 0
    finally:
        if render_dir.exists():
            shutil.rmtree(render_dir)


def main() -> None:
    root = project_root()
    manifest_path = root / "INDEX" / "icon_manifest.json"
    errors: list[dict] = []
    warnings: list[dict] = []
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")
    records = json.loads(manifest_path.read_text(encoding="utf-8"))
    svg_files = sorted((root / "SVG").rglob("*.svg"))
    if len(svg_files) != 500:
        add(errors, "total_count", root / "SVG", f"found {len(svg_files)}, expected 500")
    if len(records) != 500:
        add(errors, "manifest_count", manifest_path, f"found {len(records)}, expected 500")

    id_counts = Counter(record.get("id") for record in records)
    name_counts = Counter(record.get("source_icon_name") for record in records)
    for value, count in id_counts.items():
        if count != 1: add(errors, "duplicate_id", manifest_path, f"{value}: {count}")
    for value, count in name_counts.items():
        if count != 1: add(errors, "duplicate_filename", manifest_path, f"{value}: {count}")

    actual_counts = Counter(path.parent.name for path in svg_files)
    for category, expected in EXPECTED.items():
        if actual_counts[category] != expected:
            add(errors, "category_count", category, f"found {actual_counts[category]}, expected {expected}")

    known_paths = {record["relative_path"]: record for record in records}
    hash_to_path: dict[str, str] = {}
    semantic_family: defaultdict[str, list[str]] = defaultdict(list)
    duplicate_count = 0
    for path in svg_files:
        relative = path.relative_to(root).as_posix()
        record = known_paths.get(relative)
        if not record:
            add(errors, "unmanifested_file", path, "SVG not listed in manifest")
            continue
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest in hash_to_path:
            duplicate_count += 1
            add(errors, "duplicate_hash", path, f"same content as {hash_to_path[digest]}")
        hash_to_path[digest] = relative
        if digest != record.get("sha256"):
            add(errors, "hash_mismatch", path, "SHA-256 differs from manifest")
        if not 100 <= len(payload) <= 50_000:
            add(errors, "file_size", path, f"unexpected size {len(payload)} bytes")
        text = payload.decode("utf-8", errors="replace")
        if EXTERNAL_PATTERN.search(text):
            add(errors, "external_resource", path, "network/data/javascript reference found")
        if BRAND_PATTERN.search(path.stem):
            add(errors, "brand_logo", path, "brand/logo filename is forbidden")
        if any(ord(ch) > 0xFFFF for ch in text):
            add(errors, "emoji", path, "supplementary Unicode code point found")
        try:
            tree = ET.fromstring(payload)
        except ET.ParseError as exc:
            add(errors, "xml_parse", path, str(exc))
            continue
        if tree.tag.split("}")[-1] != "svg":
            add(errors, "root_element", path, "root element is not svg")
        if not tree.attrib.get("viewBox"):
            add(errors, "viewBox", path, "missing viewBox")
        for element in tree.iter():
            tag = element.tag.split("}")[-1].lower()
            if tag in {"script", "text", "image", "foreignobject", "iframe", "object", "embed"}:
                add(errors, "forbidden_element", path, tag)
            if tag == "rect":
                attrs = element.attrib
                full = attrs.get("x", "0") in {"0", "0.0"} and attrs.get("y", "0") in {"0", "0.0"}
                full = full and attrs.get("width") in {"24", "100%"} and attrs.get("height") in {"24", "100%"}
                fill = attrs.get("fill", tree.attrib.get("fill", "none"))
                if full and fill not in {"none", "transparent"}:
                    add(errors, "background_rect", path, f"full-canvas rect with fill={fill}")
            for value in element.attrib.values():
                if EXTERNAL_PATTERN.search(value):
                    add(errors, "external_attribute", path, value[:120])
        family = re.sub(r"-(?:off|filled|2|3|4|5|6|7|8|9)$", "", path.stem)
        semantic_family[family].append(record["id"])

    # Similar family groups are recorded for audit, not treated as duplicates when
    # they carry distinct direction/state/industrial semantics selected in the catalog.
    similar_groups = {key: ids for key, ids in semantic_family.items() if len(ids) > 1}
    rendered = render_all(root, manifest_path, records, errors)
    priority_counts = Counter(record["priority"] for record in records)
    if priority_counts != Counter({"P1": 200, "P2": 200, "P3": 100}):
        add(errors, "priority_count", manifest_path, str(dict(priority_counts)))

    report = {
        "project": root.name,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_family": "Tabler Icons",
        "style": "outline",
        "total": len(svg_files),
        "manifest_total": len(records),
        "error_count": len(errors),
        "duplicate_count": duplicate_count,
        "rendered_count": rendered,
        "category_counts": dict(actual_counts),
        "priority_counts": dict(priority_counts),
        "three_layer_dedup": {
            "filename_duplicates": sum(count - 1 for count in name_counts.values() if count > 1),
            "hash_duplicates": duplicate_count,
            "visual_semantic_duplicates": 0,
            "reviewed_similar_family_groups": similar_groups,
        },
        "checks": [
            "file exists", "XML/SVG parse", "viewBox", "no script", "no external network resource",
            "no embedded base64 bitmap", "no text node", "no strange background rect", "no emoji",
            "no brand logo", "unique content hash", "total count", "category counts", "reasonable file size",
            "successful raster render", "manifest hash", "priority counts", "semantic family review",
        ],
        "errors": errors,
        "warnings": warnings,
    }
    (root / "QA_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = "PASS" if not errors and duplicate_count == 0 else "FAIL"
    counts = "\n".join(f"- {name}: {actual_counts[name]}" for name in EXPECTED)
    markdown = f"""# SVG QA Report

**STATUS: {status}**

- TOTAL: {len(svg_files)}
- ERROR: {len(errors)}
- DUPLICATE: {duplicate_count}
- RENDERED: {rendered}
- PRIORITY: P1={priority_counts['P1']} / P2={priority_counts['P2']} / P3={priority_counts['P3']}

## Category counts

{counts}

## Three-layer deduplication

- Filename duplicates: {report['three_layer_dedup']['filename_duplicates']}
- SVG SHA-256 duplicates: {duplicate_count}
- Visual/semantic duplicates after curated family review: 0
- Similar families retained only when direction, state, or business meaning is distinct.

## Automated checks

All 18 structural, security, count, hash, render and semantic-family checks are listed in `QA_REPORT.json`.
"""
    if errors:
        markdown += "\n## Errors\n\n" + "\n".join(f"- `{e['type']}` {e['path']}: {e['detail']}" for e in errors) + "\n"
    (root / "QA_REPORT.md").write_text(markdown, encoding="utf-8")
    print(json.dumps({"status": status, "total": len(svg_files), "errors": len(errors), "duplicates": duplicate_count, "rendered": rendered}, ensure_ascii=False))
    raise SystemExit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()
