#!/usr/bin/env python3
"""Build the curated PPT icon library from an official Tabler checkout."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

from selection_catalog import ALIASES_ZH, CATALOG, CATEGORIES, CATEGORY_KEYWORDS_EN

PROJECT_NAME = "PPT_ICON_LIBRARY_500_v1.0"
REPOSITORY = "https://github.com/tabler/tabler-icons"
LICENSE_NAME = "MIT"
FIELDNAMES = [
    "id", "source_icon_name", "name_zh", "name_en", "category",
    "keywords_zh", "keywords_en", "aliases_zh", "priority", "source_family",
    "style", "stroke_width", "viewBox", "relative_path", "source_repository",
    "license", "sha256", "selection_score_total", "selection_score",
]


def read_svg_metadata(path: Path) -> tuple[str, str]:
    root = ET.parse(path).getroot()
    return root.attrib.get("stroke-width", "2"), root.attrib.get("viewBox", "")


def score(category: str, index: int, p1_count: int) -> dict[str, int]:
    profiles = {
        "01": (5, 5, 5, 3, 2), "02": (5, 5, 5, 3, 2),
        "03": (5, 4, 5, 5, 3), "04": (5, 5, 5, 5, 3),
        "05": (5, 5, 5, 4, 2), "06": (5, 4, 4, 5, 4),
        "07": (5, 3, 3, 5, 4), "08": (5, 4, 4, 5, 4),
        "09": (5, 3, 3, 5, 3), "10": (5, 5, 5, 5, 3),
        "11": (5, 4, 4, 4, 4), "12": (5, 3, 3, 4, 5),
    }
    ppt, industrial, manufacturing, management, research = profiles[category[:2]]
    tier = 0 if index <= p1_count else (1 if index <= p1_count * 2 else 2)
    return {
        "ppt_usefulness": max(3, ppt - (1 if tier == 2 else 0)),
        "industrial_relevance": max(2, industrial - (1 if tier == 2 else 0)),
        "manufacturing_relevance": max(2, manufacturing - (1 if tier == 2 else 0)),
        "management_relevance": max(2, management - (1 if tier == 2 else 0)),
        "research_education_relevance": max(2, research - (1 if tier == 2 else 0)),
        "small_size_legibility": 5 if tier == 0 else 4,
        "confusion_resistance": 5 if tier == 0 else 4,
        "niche_resistance": 5 if tier == 0 else (4 if tier == 1 else 3),
        "formal_presentation_fit": 5 if tier < 2 else 4,
        "duplicate_resistance": 5,
    }


def aliases_for(name_zh: str, keywords: list[str]) -> list[str]:
    text = " ".join([name_zh, *keywords])
    found = []
    for alias, canonical in ALIASES_ZH.items():
        if canonical in text or any(piece and piece in text for piece in re.split(r"[管理维护分析运输]", canonical)):
            found.append(alias)
    return sorted(set(found))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build(source: Path, output: Path) -> None:
    outline = source / "icons" / "outline"
    if not outline.is_dir():
        raise SystemExit(f"Tabler outline directory not found: {outline}")

    selected = [item[0] for category in CATALOG.values() for item in category]
    if len(selected) != 500 or len(set(selected)) != 500:
        raise SystemExit(f"Catalog must contain 500 unique names; got {len(selected)}/{len(set(selected))}")

    for category, _code, expected, _p1 in CATEGORIES:
        if len(CATALOG[category]) != expected:
            raise SystemExit(f"{category}: expected {expected}, got {len(CATALOG[category])}")

    for folder in ["LICENSES", "SVG", "INDEX", "PREVIEW", "TOOLS", "PROJECT_UPLOAD"]:
        (output / folder).mkdir(parents=True, exist_ok=True)
    for category, *_ in CATEGORIES:
        (output / "SVG" / category).mkdir(parents=True, exist_ok=True)

    records = []
    hashes: dict[str, str] = {}
    semantic: dict[str, list[str]] = defaultdict(list)
    priority_index: dict[str, list[str]] = {"P1": [], "P2": [], "P3": []}

    for category, code, expected, p1_count in CATEGORIES:
        for index, (source_name, name_zh, keywords_zh) in enumerate(CATALOG[category], 1):
            src = outline / f"{source_name}.svg"
            if not src.is_file():
                raise SystemExit(f"Missing official Tabler icon: {source_name}")
            dst = output / "SVG" / category / src.name
            shutil.copyfile(src, dst)
            payload = dst.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            if digest in hashes:
                raise SystemExit(f"Duplicate SVG content: {source_name} == {hashes[digest]}")
            hashes[digest] = source_name
            stroke_width, view_box = read_svg_metadata(dst)
            icon_id = f"{code}-{index:03d}"
            priority = "P1" if index <= p1_count else ("P2" if index <= p1_count * 2 else "P3")
            category_en = CATEGORY_KEYWORDS_EN[category]
            keywords_en = list(dict.fromkeys([*category_en, *source_name.split("-"), source_name]))
            icon_aliases = aliases_for(name_zh, keywords_zh)
            selection_score = score(category, index, p1_count)
            relative_path = (Path("SVG") / category / src.name).as_posix()
            record = {
                "id": icon_id,
                "source_icon_name": source_name,
                "name_zh": name_zh,
                "name_en": source_name,
                "category": category,
                "keywords_zh": list(dict.fromkeys([name_zh, *keywords_zh])),
                "keywords_en": keywords_en,
                "aliases_zh": icon_aliases,
                "priority": priority,
                "source_family": "Tabler Icons",
                "style": "outline",
                "stroke_width": stroke_width,
                "viewBox": view_box,
                "relative_path": relative_path,
                "source_repository": "tabler/tabler-icons",
                "license": LICENSE_NAME,
                "sha256": digest,
                "selection_score_total": sum(selection_score.values()),
                "selection_score": selection_score,
            }
            records.append(record)
            priority_index[priority].append(icon_id)
            for term in dict.fromkeys([name_zh, category[3:], *keywords_zh, *icon_aliases]):
                if term:
                    semantic[term].append(icon_id)

    write_json(output / "INDEX" / "icon_manifest.json", records)
    with (output / "INDEX" / "icon_manifest.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        for record in records:
            row = dict(record)
            for key in ["keywords_zh", "keywords_en", "aliases_zh"]:
                row[key] = "|".join(row[key])
            row["selection_score"] = json.dumps(row["selection_score"], ensure_ascii=False, separators=(",", ":"))
            writer.writerow(row)
    write_json(output / "INDEX" / "semantic_index_zh.json", dict(sorted(semantic.items())))
    write_json(output / "INDEX" / "aliases_zh.json", ALIASES_ZH)
    write_json(output / "INDEX" / "priority_index.json", priority_index)

    shutil.copyfile(source / "LICENSE", output / "LICENSES" / "TABLER_LICENSE.txt")
    commit = "unknown"
    head = source / ".git" / "HEAD"
    if head.exists():
        raw = head.read_text(encoding="utf-8").strip()
        ref = raw.split(" ", 1)[1] if raw.startswith("ref: ") else ""
        ref_file = source / ".git" / ref
        commit = ref_file.read_text(encoding="utf-8").strip() if ref_file.exists() else raw

    counts_md = "\n".join(f"- {cat}: {count}" for cat, _code, count, _p1 in CATEGORIES)
    readme = f"""# {PROJECT_NAME}

面向中文 PPT、工业工程、制造业、企业管理与科研教学的本地专业 SVG 图标库。

## 概览

- 总数：500 个唯一 SVG
- 风格：Tabler Icons outline，24×24 viewBox，默认 stroke-width 2
- 优先级：P1 200 / P2 200 / P3 100
- 来源：[{REPOSITORY}]({REPOSITORY})
- Source family：Tabler Icons
- Source repository：tabler/tabler-icons
- Source commit：`{commit}`
- License：MIT
- Retrieval date：{date.today().isoformat()}

## 分类数量

{counts_md}

## 使用

```powershell
python TOOLS/search_icons.py "设备维护"
python TOOLS/qa_icons.py
python TOOLS/build_contact_sheets.py
```

搜索工具仅使用 Python 标准库，不联网。QA 与预览渲染优先使用 Node.js `sharp`，也支持环境变量 `NODE_PATH` 指向已安装的 sharp。

## 索引

- `INDEX/icon_manifest.json` / `.csv`：完整元数据、SHA-256、优先级与 10 维筛选评分。
- `INDEX/semantic_index_zh.json`：中文语义到 icon ID 的反向索引。
- `INDEX/aliases_zh.json`：中文自然语言别名归一化。
- `INDEX/priority_index.json`：P1/P2/P3 分组。

## 筛选原则

图标按 PPT 通用性、工业工程、制造业、企业管理、科研教学、16–32px 辨识度、混淆风险、小众程度、正式汇报适配度和近似重复风险十项审查。排除品牌 Logo、娱乐、宗教、地域化和过度生活化图标。三层去重覆盖源文件名、SVG 内容 SHA-256 与视觉/语义家族人工审查。

## 授权

所有 SVG 均来自 Tabler Icons 官方仓库，按 MIT License 使用。完整许可见 `LICENSES/TABLER_LICENSE.txt`。
"""
    (output / "README.md").write_text(readme, encoding="utf-8")

    integration = f"""# {PROJECT_NAME} — PPT 4.0 集成说明

## WF4 视觉资产调用优先级

1. LOCAL ICON LIBRARY
2. Online mature SVG library
3. PPT Native Shape
4. AI icon generation（default OFF）

## 调用链

用户文本 → Visual Router 判定 `ICON` → `TOOLS/search_icons.py` 本地检索 → 返回 Top candidates → 按当前 Design DNA 筛选 → Palette Engine 统一着色 → Asset QA → 插入 PPT。

若 Visual Router 输出 `NONE`，不得为了装饰强行添加图标。ICON 不是必需视觉元素。

## 建议调用

```powershell
python TOOLS/search_icons.py "设备维护" --json
python TOOLS/search_icons.py "人员培训" --limit 10
```

渲染时保留 `viewBox`、纵横比和 outline，不写入固定品牌色。图标颜色由 PPT 4.0 Palette Engine 在插入阶段统一决定。

## 文件约定

- 使用 manifest 中的 `relative_path` 定位 SVG。
- 首选 `P1`，语义不足时再扩展到 `P2`、`P3`。
- 使用 `aliases_zh.json` 归一化口语与行业简称。
- 插入前核对 `sha256`，并执行 Asset QA。
"""
    (output / "PROJECT_UPLOAD" / "README_for_PPT4.0.md").write_text(integration, encoding="utf-8")
    shutil.copyfile(output / "INDEX" / "icon_manifest.json", output / "PROJECT_UPLOAD" / "icon_manifest.json")
    shutil.copyfile(output / "INDEX" / "semantic_index_zh.json", output / "PROJECT_UPLOAD" / "semantic_index_zh.json")

    tool_source = Path(__file__).resolve().parent
    for name in ["selection_catalog.py", "build_library.py", "search_icons.py", "qa_icons.py", "build_contact_sheets.py", "render_svg_batch.js"]:
        candidate = tool_source / name
        if candidate.exists():
            shutil.copyfile(candidate, output / "TOOLS" / name)
    print(f"Built {len(records)} icons at {output}")


if __name__ == "__main__":
    workspace = Path(__file__).resolve().parents[1]
    source_arg = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else workspace / ".tabler-source"
    output_arg = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else workspace / PROJECT_NAME
    build(source_arg, output_arg)
