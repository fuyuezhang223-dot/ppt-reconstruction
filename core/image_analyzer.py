"""OCR-assisted image analysis for editable-PPT reconstruction.

The module deliberately emits a REVIEWABLE draft rather than claiming semantic
understanding of arbitrary slide screenshots. OCR text is normalized to the
existing page-spec contract; visual regions are proposals only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import shutil

from PIL import Image, ImageDraw, ImageOps
from .icon_library import IconLibrary
from .structure_analyzer import analyze_structure

SUPPORTED_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff'}


@dataclass
class OCRItem:
    text: str
    bbox_px: list[int]
    confidence: float
    engine: str

    def normalized(self, width: int, height: int) -> dict[str, Any]:
        x1, y1, x2, y2 = self.bbox_px
        x1 = max(0, min(width - 1, int(x1)))
        y1 = max(0, min(height - 1, int(y1)))
        x2 = max(x1 + 1, min(width, int(x2)))
        y2 = max(y1 + 1, min(height, int(y2)))
        return {
            'text': self.text,
            'bbox_px': [x1, y1, x2, y2],
            'bbox_norm': [round(x1 / width, 6), round(y1 / height, 6),
                          round((x2 - x1) / width, 6), round((y2 - y1) / height, 6)],
            'confidence': round(max(0.0, min(1.0, float(self.confidence))), 4),
            'engine': self.engine,
        }


def _rapidocr(path: Path) -> list[OCRItem]:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception as exc:
        raise RuntimeError('未安装 rapidocr_onnxruntime') from exc
    engine = RapidOCR()
    # Normalize EXIF orientation and avoid Windows OpenCV path issues for Chinese filenames.
    import numpy as np
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert('RGB')
        image_array = np.asarray(image)[:, :, ::-1].copy()  # RapidOCR ndarray input is BGR.
    result = engine(image_array)
    rows = result[0] if isinstance(result, tuple) else result
    items: list[OCRItem] = []
    for row in rows or []:
        try:
            points, text, score = row[0], str(row[1]).strip(), float(row[2])
            if not text:
                continue
            xs = [float(p[0]) for p in points]
            ys = [float(p[1]) for p in points]
            items.append(OCRItem(text, [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))], score, 'rapidocr'))
        except (TypeError, ValueError, IndexError):
            continue
    return items


def _tesseract(path: Path, lang: str) -> list[OCRItem]:
    try:
        import pytesseract
        from pytesseract import Output
    except Exception as exc:
        raise RuntimeError('未安装 pytesseract') from exc
    command = str(getattr(pytesseract.pytesseract, 'tesseract_cmd', 'tesseract'))
    if not Path(command).is_file() and not shutil.which(command):
        raise RuntimeError('未找到 Tesseract 可执行程序；请安装 Tesseract 并配置 PATH')
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert('RGB')
        data = pytesseract.image_to_data(image, lang=lang, config='--psm 6', output_type=Output.DICT)
    grouped: dict[tuple[int, int, int], list[int]] = {}
    texts: dict[tuple[int, int, int], list[str]] = {}
    confs: dict[tuple[int, int, int], list[float]] = {}
    for i, raw in enumerate(data.get('text', [])):
        text = str(raw).strip()
        try:
            confidence = float(data['conf'][i]) / 100.0
        except (ValueError, TypeError, KeyError):
            confidence = 0.0
        if not text or confidence < 0:
            continue
        key = (int(data['block_num'][i]), int(data['par_num'][i]), int(data['line_num'][i]))
        x, y = int(data['left'][i]), int(data['top'][i])
        w, h = int(data['width'][i]), int(data['height'][i])
        if key not in grouped:
            grouped[key] = [x, y, x + w, y + h]
            texts[key] = [text]
            confs[key] = [max(0.0, confidence)]
        else:
            box = grouped[key]
            box[0] = min(box[0], x); box[1] = min(box[1], y)
            box[2] = max(box[2], x + w); box[3] = max(box[3], y + h)
            texts[key].append(text); confs[key].append(max(0.0, confidence))
    return [OCRItem(' '.join(texts[k]), grouped[k], sum(confs[k]) / len(confs[k]), 'tesseract')
            for k in grouped]


def run_ocr(path: Path, engine: str = 'auto', lang: str = 'chi_sim+eng') -> tuple[list[OCRItem], str, list[str]]:
    warnings: list[str] = []
    choices = ['rapidocr', 'tesseract'] if engine == 'auto' else [engine]
    for choice in choices:
        try:
            if choice == 'rapidocr':
                items = _rapidocr(path)
            elif choice == 'tesseract':
                items = _tesseract(path, lang)
            elif choice == 'none':
                return [], 'none', ['未执行 OCR：仅生成图片元数据，需人工录入页面内容。']
            else:
                raise ValueError(f'不支持的 OCR 引擎：{choice}')
            if engine == 'auto' and choice == 'rapidocr' and not items:
                warnings.append('RapidOCR 未识别到文字，继续尝试 Tesseract。')
                continue
            return items, choice, warnings
        except Exception as exc:
            warnings.append(f'{choice} 不可用：{exc}')
            if engine != 'auto':
                raise RuntimeError(warnings[-1]) from exc
    raise RuntimeError('没有可用的 OCR 引擎。请安装 requirements-image-analysis.txt，或安装 Tesseract。\n' + '\n'.join(warnings))


def _hex(rgb: tuple[int, int, int]) -> str:
    return '#%02X%02X%02X' % tuple(max(0, min(255, int(v))) for v in rgb)


def _guess_background(image: Image.Image) -> str:
    rgb = image.convert('RGB')
    w, h = rgb.size
    pts = [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3), (w // 2, 2)]
    samples = [rgb.getpixel((max(0, x), max(0, y))) for x, y in pts]
    avg = tuple(round(sum(p[c] for p in samples) / len(samples)) for c in range(3))
    if min(avg) > 238:
        return '#FFFFFF'
    return _hex(avg)


def detect_rectangular_regions(path: Path, max_regions: int = 80) -> tuple[list[dict[str, Any]], list[str]]:
    """Optional OpenCV proposal detector. It never asserts semantic element type."""
    try:
        import cv2
        import numpy as np
    except Exception:
        return [], ['未安装 OpenCV，跳过矩形区域候选检测；OCR 文字识别不受影响。']
    try:
        encoded = np.fromfile(str(path), dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    except Exception:
        image = cv2.imread(str(path))
    if image is None:
        return [], ['OpenCV 无法读取图片，跳过区域检测。']
    height, width = image.shape[:2]
    scale = min(1.0, 1500.0 / max(width, height))
    if scale < 1:
        image = cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 45, 135)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 7))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue
        approx = cv2.approxPolyDP(contour, 0.025 * perimeter, True)
        if len(approx) != 4 or not cv2.isContourConvex(approx):
            continue
        x, y, rw, rh = cv2.boundingRect(approx)
        area = rw * rh
        area_ratio = area / float(w * h)
        if area_ratio < 0.0035 or area_ratio > 0.88 or rw / max(rh, 1) > 30 or rh / max(rw, 1) > 20:
            continue
        if rw / max(rh, 1) < 0.12:
            continue
        # Use the median interior color as a visual hint only.
        pad_x, pad_y = max(1, int(rw * .12)), max(1, int(rh * .12))
        roi = image[min(h-1, y+pad_y):max(y+pad_y+1, min(h, y+rh-pad_y)),
                    min(w-1, x+pad_x):max(x+pad_x+1, min(w, x+rw-pad_x))]
        if roi.size == 0:
            continue
        bgr = np.median(roi.reshape(-1, 3), axis=0)
        fill = _hex((int(bgr[2]), int(bgr[1]), int(bgr[0])))
        # Restore original pixel coordinates after optional downscaling.
        ox, oy, ow, oh = [int(round(v / scale)) for v in (x, y, rw, rh)]
        candidates.append({'bbox_px': [ox, oy, ox + ow, oy + oh],
                           'bbox_norm': [round(ox / width, 6), round(oy / height, 6),
                                         round(ow / width, 6), round(oh / height, 6)],
                           'fill_hint': fill, 'area_ratio': round(area_ratio, 5),
                           'confidence': 0.35, 'source': 'opencv_rectangular_contour',
                           'review_required': True})
    # Keep large candidates and suppress near-duplicates/nested contour copies.
    candidates.sort(key=lambda x: x['area_ratio'], reverse=True)
    kept: list[dict[str, Any]] = []
    for item in candidates:
        x, y, bw, bh = item['bbox_norm']
        duplicate = False
        for old in kept:
            ox, oy, ow, oh = old['bbox_norm']
            ix = max(0.0, min(x+bw, ox+ow) - max(x, ox))
            iy = max(0.0, min(y+bh, oy+oh) - max(y, oy))
            inter = ix * iy
            union = bw*bh + ow*oh - inter
            if union and inter / union > 0.84:
                duplicate = True; break
        if not duplicate:
            kept.append(item)
        if len(kept) >= max_regions:
            break
    return kept, []


def _font_size_from_box(box_norm: list[float], slide_height_pt: float = 540.0) -> float:
    # Glyph height is usually smaller than nominal font size; this is a rough seed only.
    estimate = box_norm[3] * slide_height_pt / 0.72
    return round(max(8.0, min(48.0, estimate)), 1)


def _infer_align(box: list[float]) -> str:
    center = box[0] + box[2] / 2
    if abs(center - 0.5) < 0.075:
        return 'center'
    return 'left'


def make_draft_spec(image_path: Path, image_info: dict[str, Any], ocr_items: list[dict[str, Any]],
                    regions: list[dict[str, Any]], min_confidence: float = 0.75,
                    page_width_in: float | None = None, page_height_in: float = 7.5,
                    structure: dict[str, Any] | None = None) -> dict[str, Any]:
    ratio = image_info['width'] / image_info['height']
    if page_width_in is None:
        page_width_in = round(page_height_in * ratio, 4)
    elements: list[dict[str, Any]] = []
    # Background panels are deliberately low-confidence proposals and are placed behind text.
    for i, region in enumerate(regions, 1):
        elements.append({'type': 'shape', 'id': f'candidate_region_{i:03d}',
                         'shape': 'rect', 'bbox_norm': region['bbox_norm'],
                         'fill': region.get('fill_hint', '#FFFFFF'),
                         'confidence': region.get('confidence', 0.35),
                         'needs_review': True, 'source': 'opencv_candidate_region'})
    # Add only non-rectangular geometry proposals here; rectangles are already
    # represented by the legacy panel detector to avoid duplicate outlines.
    if structure:
        nonrect = [x for x in structure.get('shape_candidates', []) if x.get('shape') in {'ellipse', 'diamond', 'triangle'}]
        for i, item in enumerate(nonrect, 1):
            elements.append({'type': 'shape', 'id': f'candidate_geometry_{i:03d}',
                             'shape': item['shape'], 'bbox_norm': item['bbox_norm'],
                             'fill': 'none', 'line_color': '#8A94A6', 'line_width': 0.8,
                             'confidence': item.get('confidence', 0.45),
                             'needs_review': True, 'source': item.get('source', 'opencv_geometry')})
        for i, item in enumerate(structure.get('connector_candidates', []), 1):
            elements.append({'type': 'connector', 'id': f'candidate_arrow_{i:03d}',
                             'points_norm': item['points_norm'], 'arrow': 'end',
                             'color': '#8A94A6', 'line_width': 1.4,
                             'confidence': item.get('confidence', 0.55),
                             'needs_review': True, 'source': item.get('source', 'opencv_arrow')})
        for i, item in enumerate(structure.get('table_candidates', []), 1):
            rows = item.get('suggested_rows') or []
            if rows and len(rows) >= 2 and len(rows[0]) >= 2 and item.get('ocr_cells_filled', 0) >= 3:
                elements.append({'type': 'table', 'id': f'candidate_table_{i:03d}',
                                 'bbox_norm': item['bbox_norm'], 'rows': rows,
                                 'font_size': 9, 'confidence': item.get('confidence', 0.5),
                                 'needs_review': True, 'source': 'opencv_grid_plus_ocr'})
    sorted_items = sorted(ocr_items, key=lambda item: (item['bbox_px'][1], item['bbox_px'][0]))
    for i, item in enumerate(sorted_items, 1):
        box = item['bbox_norm']
        confidence = float(item['confidence'])
        elements.append({'type': 'text', 'id': f'ocr_text_{i:03d}',
                         'bbox_norm': box, 'text': item['text'],
                         'font_size': _font_size_from_box(box, slide_height_pt=page_height_in * 72.0),
                         'align': _infer_align(box), 'v_align': 'middle',
                         'confidence': confidence,
                         'needs_review': confidence < min_confidence,
                         'source': 'ocr', 'source_bbox_px': item['bbox_px']})
    warnings = []
    if not ocr_items:
        warnings.append('没有提取到文字；请人工建立页面元素。')
    if any(x['needs_review'] for x in elements if x['type'] == 'text'):
        warnings.append('存在低置信度 OCR 文本，必须对照原图核对。')
    if regions:
        warnings.append('矩形区域为视觉候选，不代表已识别为卡片/面板；请人工确认后保留或删除。')
    if structure:
        if structure.get('connector_candidates'):
            warnings.append('已提出箭头/连线候选；方向和端点需逐条核对。')
        if structure.get('table_candidates'):
            warnings.append('已提出表格网格候选；请核对行列和单元格文字。')
        if structure.get('icon_candidates'):
            warnings.append('已定位图标候选；SVG 建议来自邻近 OCR 标签语义检索，不是视觉同一性证明。')
    page = {'page_id': 'slide_001', 'source_type': 'ocr_assisted_draft',
            'reference_image': str(image_path.resolve()),
            'background': image_info.get('background_hint', '#FFFFFF'),
            'elements': elements, 'review_required': True, 'review_warnings': warnings}
    if structure:
        page['icon_suggestions'] = structure.get('icon_candidates', [])
        page['layout_hypotheses'] = structure.get('layout_hypotheses', [])
        page['structure_summary'] = {
            'shape_candidates': len(structure.get('shape_candidates', [])),
            'table_candidates': len(structure.get('table_candidates', [])),
            'connector_candidates': len(structure.get('connector_candidates', [])),
            'icon_candidates': len(structure.get('icon_candidates', []))}
    return {
        'route': 'strict_reconstruction',
        'slide_size_in': [page_width_in, page_height_in],
        'source_image': str(image_path.resolve()),
        'source_type': 'ocr_assisted_draft',
        'analysis_status': 'REVIEW_REQUIRED',
        'pages': [page],
        'generation_notes': [
            '本文件是 OCR 辅助初稿，不是自动完成的高保真复刻。',
            '文字坐标来自 OCR；字号、对齐和背景色为启发式估计。',
            '候选矩形/几何/箭头/表格均需人工确认；图标建议仅基于邻近 OCR 标签语义检索。',
            '请核对文字、元素层级、连接关系和参考图比例后再正式交付。'
        ]
    }


def draw_overlay(image_path: Path, items: list[dict[str, Any]], out_path: Path,
                 min_confidence: float = 0.75, structure: dict[str, Any] | None = None) -> None:
    """Render OCR and visual-structure proposals on the source image for review."""
    with Image.open(image_path) as src:
        image = ImageOps.exif_transpose(src).convert('RGB')
    draw = ImageDraw.Draw(image)
    line_w = max(2, image.width // 700)
    # Geometric shape proposals: amber.
    if structure:
        for item in structure.get('shape_candidates', []):
            x1, y1, x2, y2 = item['bbox_px']
            draw.rectangle((x1, y1, x2, y2), outline='#D97706', width=line_w)
            draw.text((x1 + 2, max(0, y1 - 16)), f"shape:{item['shape']}", fill='#B45309')
        # Table/grid proposals: blue.
        for item in structure.get('table_candidates', []):
            x1, y1, x2, y2 = item['bbox_px']
            draw.rectangle((x1, y1, x2, y2), outline='#2563EB', width=line_w + 1)
            draw.text((x1 + 3, max(0, y1 - 18)),
                      f"table:{item['row_count']}x{item['column_count']}", fill='#1D4ED8')
        # Arrow proposals: purple, with a visible triangular tip.
        for item in structure.get('connector_candidates', []):
            x1, y1, x2, y2 = item['points_px']
            draw.line((x1, y1, x2, y2), fill='#9333EA', width=line_w + 1)
            import math
            angle = math.atan2(y2 - y1, x2 - x1)
            size = max(8, image.width // 120)
            p1 = (x2, y2)
            p2 = (x2 - size * math.cos(angle - .55), y2 - size * math.sin(angle - .55))
            p3 = (x2 - size * math.cos(angle + .55), y2 - size * math.sin(angle + .55))
            draw.polygon((p1, p2, p3), fill='#9333EA')
    # OCR boxes: green = above confidence threshold; red = manual review.
    for i, item in enumerate(items, 1):
        x1, y1, x2, y2 = item['bbox_px']
        color = '#16A34A' if item['confidence'] >= min_confidence else '#DC2626'
        draw.rectangle((x1, y1, x2, y2), outline=color, width=line_w)
        label = f"OCR {i} | {item['confidence']:.2f}"
        draw.rectangle((x1, max(0, y1-18), x1+len(label)*7+6, y1), fill=color)
        draw.text((x1+3, max(0, y1-17)), label, fill='white')
    # Draw icon candidates last so a compact icon remains visible even when OCR
    # merged it into the neighboring text box (e.g. "Q Factory").
    if structure:
        for item in structure.get('icon_candidates', []):
            x1, y1, x2, y2 = item['bbox_px']
            draw.rectangle((x1, y1, x2, y2), outline='#0891B2', width=line_w + 1)
            suggestion = item.get('icon_suggestions') or []
            label = suggestion[0]['icon_id'] if suggestion else 'icon?'
            draw.text((x1 + 2, min(image.height - 12, y2 + 2)), label, fill='#0E7490')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def analyze_one(path: Path, engine: str = 'auto', lang: str = 'chi_sim+eng',
                min_confidence: float = 0.75, detect_shapes: bool = True,
                page_height_in: float = 7.5) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[str]]:
    with Image.open(path) as src:
        image = ImageOps.exif_transpose(src).convert('RGB')
        width, height = image.size
        info = {'width': width, 'height': height, 'aspect_ratio': round(width / height, 6),
                'orientation': 'landscape' if width > height else ('portrait' if height > width else 'square'),
                'background_hint': _guess_background(image)}
    items, used_engine, warnings = run_ocr(path, engine=engine, lang=lang)
    normalized = [item.normalized(width, height) for item in items]
    regions: list[dict[str, Any]] = []
    structure: dict[str, Any] = {}
    if detect_shapes:
        regions, region_warnings = detect_rectangular_regions(path)
        warnings.extend(region_warnings)
        try:
            structure = analyze_structure(path, normalized, IconLibrary())
            warnings.extend(structure.get('warnings', []))
            # A detected table grid supersedes its outer rectangular-panel proposal.
            table_boxes = [x['bbox_norm'] for x in structure.get('table_candidates', [])]
            if table_boxes:
                kept_regions = []
                for region in regions:
                    x, y, w, h = region['bbox_norm']
                    cx, cy = x + w / 2, y + h / 2
                    if not any(tx <= cx <= tx + tw and ty <= cy <= ty + th
                               for tx, ty, tw, th in table_boxes):
                        kept_regions.append(region)
                regions = kept_regions
        except Exception as exc:
            warnings.append(f'结构分析未完成：{exc}')
    report = {'schema_version': '1.2', 'source_image': str(path.resolve()),
              'image': info, 'ocr': {'engine': used_engine, 'item_count': len(normalized),
                                     'min_confidence_threshold': min_confidence,
                                     'items': normalized},
              'candidate_regions': regions, 'structure': structure, 'warnings': warnings,
              'limitations': ['OCR 不等于版面语义理解。', '轮廓几何不能单独证明卡片、表格或流程节点的业务含义。',
                              '箭头方向、表格单元格、图标语义、图表数据和文本逻辑需人工或视觉模型复核。',
                              '图标候选依据邻近 OCR 标签检索 500 SVG 库，不是像素级视觉分类。']}
    draft = make_draft_spec(path, info, normalized, regions, min_confidence=min_confidence,
                            page_height_in=page_height_in, structure=structure)
    return report, draft, normalized, warnings


def collect_images(input_path: Path, exclude_dir: Path | None = None) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() not in SUPPORTED_EXTS:
            raise ValueError(f'不支持的图片格式：{input_path.suffix}')
        return [input_path]
    if input_path.is_dir():
        excluded = exclude_dir.resolve() if exclude_dir is not None else None
        files = []
        for candidate in input_path.iterdir():
            if not candidate.is_file() or candidate.suffix.lower() not in SUPPORTED_EXTS:
                continue
            resolved = candidate.resolve()
            if excluded is not None and (resolved == excluded or excluded in resolved.parents):
                continue
            files.append(candidate)
        return sorted(files)
    raise FileNotFoundError(input_path)


def analyze_batch(input_path: Path, output_dir: Path, engine: str = 'auto', lang: str = 'chi_sim+eng',
                  min_confidence: float = 0.75, detect_shapes: bool = True,
                  page_width_in: float | None = None, page_height_in: float = 7.5) -> dict[str, Any]:
    images = collect_images(input_path, exclude_dir=output_dir)
    if not images:
        raise ValueError('输入目录中没有找到支持的图片文件。')
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    reports = []
    global_warnings = []
    for index, path in enumerate(images, 1):
        report, draft, items, warnings = analyze_one(path, engine, lang, min_confidence, detect_shapes,
                                                  page_height_in=page_height_in)
        report_path = output_dir / f'analysis_{index:03d}.json'
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        overlay_path = output_dir / f'overlay_{index:03d}.png'
        draw_overlay(path, items, overlay_path, min_confidence, report.get('structure'))
        page = draft['pages'][0]
        page['page_id'] = f'slide_{index:03d}'
        pages.append(page)
        low_confidence = sum(1 for item in items if item['confidence'] < min_confidence)
        reports.append({'page_id': page['page_id'], 'source_image': str(path.resolve()),
                        'analysis_report': str(report_path.resolve()), 'overlay': str(overlay_path.resolve()),
                        'ocr_items': len(items), 'low_confidence_items': low_confidence,
                        'candidate_regions': len(report['candidate_regions']),
                        'structure_summary': {k: len(report.get('structure', {}).get(k, [])) for k in
                                              ('shape_candidates', 'table_candidates', 'connector_candidates', 'icon_candidates')},
                        'warnings': warnings})
        global_warnings.extend(warnings)
    # A PPTX has one canvas size. Flag mixed source ratios rather than silently distort.
    ratios = []
    for image_path in images:
        with Image.open(image_path) as source:
            oriented = ImageOps.exif_transpose(source)
            ratios.append(round(oriented.width / oriented.height, 3))
    if len(set(ratios)) > 1:
        global_warnings.append('输入图片宽高比不一致；草稿 PPT 使用第一页比例，其他页面坐标可能需要重新适配。')
    with Image.open(images[0]) as first_source:
        first_oriented = ImageOps.exif_transpose(first_source)
        ratio = first_oriented.width / first_oriented.height
    h_in = page_height_in
    w_in = page_width_in if page_width_in is not None else round(h_in * ratio, 4)
    draft_spec = {'route': 'strict_reconstruction', 'slide_size_in': [w_in, h_in],
                  'source_type': 'ocr_assisted_draft', 'analysis_status': 'REVIEW_REQUIRED',
                  'pages': pages,
                  'generation_notes': [
                      '本文件由 OCR 与可选矩形轮廓检测生成，仅作为可编辑重构起点。',
                      '每页文字框坐标来自 OCR；字号/对齐/背景颜色为启发式估计。',
                      '候选矩形均需人工确认，不能据此推断业务流程或图形语义。',
                      '请逐页核对文字、字号、颜色、图标、箭头、表格、图表和元素层级。'
                  ]}
    spec_path = output_dir / 'draft_spec.json'
    spec_path.write_text(json.dumps(draft_spec, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = {'schema_version': '1.1', 'status': 'REVIEW_REQUIRED', 'image_count': len(images),
               'draft_spec': str(spec_path.resolve()), 'pages': reports,
               'warnings': list(dict.fromkeys(global_warnings))}
    (output_dir / 'image_analysis_report.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary
