#!/usr/bin/env python3
"""Render 10 all-library sheets plus one sheet for each category."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def project_root() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent if (here.parent.parent / "INDEX").exists() else here.parents[1] / "PPT_ICON_LIBRARY_500_v1.0"


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def render_icons(root: Path) -> Path:
    render_dir = root / "PREVIEW" / ".rendered"
    if render_dir.exists():
        shutil.rmtree(render_dir)
    render_dir.mkdir(parents=True)
    helper = root / "TOOLS" / "render_svg_batch.js"
    result = subprocess.run(
        [shutil.which("node") or "node", str(helper), str(root / "INDEX" / "icon_manifest.json"), str(root), str(render_dir), "72"],
        text=True, capture_output=True, encoding="utf-8", timeout=240, env=os.environ.copy(), check=False,
    )
    if result.returncode:
        raise SystemExit(result.stderr or result.stdout)
    return render_dir


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, base_size: int, bold: bool = False):
    current = base_size
    while current >= 10:
        fnt = font(current, bold)
        if draw.textbbox((0, 0), text, font=fnt)[2] <= max_width:
            return fnt
        current -= 1
    return font(10, bold)


def make_sheet(root: Path, rendered: Path, records: list[dict], title: str, target: Path, columns: int = 5):
    cell_w, cell_h, margin, header_h = 250, 146, 28, 94
    rows = (len(records) + columns - 1) // columns
    width = margin * 2 + columns * cell_w
    height = header_h + rows * cell_h + margin
    canvas = Image.new("RGB", (width, height), "#f5f7f9")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, width, header_h), fill="#263746")
    draw.text((margin, 22), title, fill="white", font=font(28, True))
    draw.text((margin, 60), f"Tabler Icons · outline · {len(records)} icons", fill="#dbe4ea", font=font(15))
    for index, record in enumerate(records):
        row, col = divmod(index, columns)
        x = margin + col * cell_w
        y = header_h + row * cell_h
        draw.rounded_rectangle((x + 7, y + 7, x + cell_w - 7, y + cell_h - 7), radius=10, fill="white", outline="#d9e0e6", width=1)
        icon = Image.open(rendered / f"{record['id']}.png").convert("RGBA")
        canvas.paste(icon, (x + (cell_w - 72) // 2, y + 17), icon)
        name_font = fit_text(draw, record["name_zh"], cell_w - 24, 17, True)
        en_font = fit_text(draw, record["name_en"], cell_w - 24, 12)
        zh_box = draw.textbbox((0, 0), record["name_zh"], font=name_font)
        en_box = draw.textbbox((0, 0), record["name_en"], font=en_font)
        draw.text((x + (cell_w - (zh_box[2] - zh_box[0])) / 2, y + 91), record["name_zh"], fill="#17232d", font=name_font)
        draw.text((x + (cell_w - (en_box[2] - en_box[0])) / 2, y + 115), record["name_en"], fill="#647482", font=en_font)
        draw.text((x + 14, y + 14), record["id"], fill="#55758b", font=font(11, True))
    canvas.save(target, optimize=True)


def main() -> None:
    root = project_root()
    preview = root / "PREVIEW"
    records = json.loads((root / "INDEX" / "icon_manifest.json").read_text(encoding="utf-8"))
    rendered = render_icons(root)
    for index in range(10):
        subset = records[index * 50:(index + 1) * 50]
        make_sheet(root, rendered, subset, f"PPT ICON LIBRARY · OVERVIEW {index + 1:02d}/10", preview / f"contact_sheet_{index + 1:02d}.png")
    categories = []
    for record in records:
        if record["category"] not in categories:
            categories.append(record["category"])
    for index, category in enumerate(categories, 1):
        subset = [record for record in records if record["category"] == category]
        make_sheet(root, rendered, subset, category, preview / f"category_contact_sheet_{index:02d}.png")
    shutil.rmtree(rendered)
    print(json.dumps({"overview_sheets": 10, "category_sheets": len(categories), "total_sheets": 10 + len(categories)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
