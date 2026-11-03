"""Rule-based visual structure proposals for slide screenshot reconstruction.

This module extracts geometric evidence only. Shape, table, connector and icon
proposals remain reviewable candidates; it never claims full semantic parsing.
"""
from __future__ import annotations

from pathlib import Path
from math import hypot
from typing import Any
from collections import defaultdict
import re


def _load_cv(path: Path):
    try:
        import cv2
        import numpy as np
    except Exception as exc:
        raise RuntimeError('结构识别需要安装 opencv-python-headless') from exc
    encoded = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f'无法读取图片：{path}')
    return cv2, np, image


def _iou(a, b):
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    iw = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    ih = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def _group_positions(values, tolerance=3):
    values = sorted(int(v) for v in values)
    groups = []
    for value in values:
        if not groups or value - groups[-1][-1] > tolerance:
            groups.append([value])
        else:
            groups[-1].append(value)
    return [int(round(sum(group) / len(group))) for group in groups]


def _shape_kind(cv2, contour, approx, w, h):
    count = len(approx)
    perimeter = cv2.arcLength(contour, True)
    area = abs(cv2.contourArea(contour))
    circularity = 4.0 * 3.141592653589793 * area / max(perimeter * perimeter, 1.0)
    if circularity >= 0.72 and count >= 5:
        return 'ellipse'
    if count == 3:
        return 'triangle'
    if count == 4:
        pts = approx.reshape(-1, 2).astype(float)
        angles = []
        for i in range(4):
            a = pts[(i - 1) % 4] - pts[i]
            b = pts[(i + 1) % 4] - pts[i]
            denom = max(1e-6, float((a @ a) ** .5 * (b @ b) ** .5))
            import numpy as np
            angles.append(float(np.degrees(np.arccos(np.clip((a @ b) / denom, -1, 1)))))
        edge_angles = []
        for i in range(4):
            delta = pts[(i + 1) % 4] - pts[i]
            angle = abs(float(np.degrees(np.arctan2(delta[1], delta[0])))) % 180
            edge_angles.append(min(angle, 180 - angle))
        diagonal_edges = all(28 <= a <= 62 for a in edge_angles)
        if all(72 <= a <= 108 for a in angles) and diagonal_edges:
            return 'diamond'
        if all(72 <= a <= 108 for a in angles):
            return 'rect'
        if all((35 <= a <= 65) or (115 <= a <= 145) for a in angles):
            return 'diamond'
        return 'quadrilateral'
    return 'polygon'


def detect_shape_candidates(path: Path, max_candidates: int = 100) -> tuple[list[dict[str, Any]], list[str]]:
    """Find compact ellipse/diamond/triangle/rectangle outlines as geometry candidates."""
    try:
        cv2, np, image = _load_cv(path)
    except Exception as exc:
        return [], [str(exc)]
    height, width = image.shape[:2]
    scale = min(1.0, 1800.0 / max(width, height))
    if scale < 1:
        image = cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, 35, 120)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    found = []
    for contour in contours:
        area = abs(cv2.contourArea(contour))
        ratio = area / float(w * h)
        if ratio < 0.0006 or ratio > 0.62:
            continue
        perimeter = cv2.arcLength(contour, True)
        if perimeter < 18:
            continue
        approx = cv2.approxPolyDP(contour, 0.025 * perimeter, True)
        kind = _shape_kind(cv2, contour, approx, w, h)
        if kind not in {'rect', 'ellipse', 'diamond', 'triangle'}:
            continue
        x, y, rw, rh = cv2.boundingRect(approx)
        if rw < max(12, int(w * .012)) or rh < max(12, int(h * .012)):
            continue
        if rw / max(rh, 1) > 18 or rh / max(rw, 1) > 18:
            continue
        ox, oy, ow, oh = [int(round(v / scale)) for v in (x, y, rw, rh)]
        found.append({'shape': kind, 'bbox_px': [ox, oy, ox + ow, oy + oh],
                      'bbox_norm': [round(ox / width, 6), round(oy / height, 6),
                                    round(ow / width, 6), round(oh / height, 6)],
                      'area_ratio': round(ratio, 6), 'confidence': 0.48,
                      'source': 'opencv_contour_geometry', 'needs_review': True})
    found.sort(key=lambda item: item['area_ratio'], reverse=True)
    kept = []
    for item in found:
        if any(_iou(item['bbox_norm'], old['bbox_norm']) > .68 for old in kept):
            continue
        kept.append(item)
        if len(kept) >= max_candidates:
            break
    return kept, []


def detect_table_candidates(path: Path, ocr_items: list[dict[str, Any]] | None = None,
                             max_candidates: int = 20) -> tuple[list[dict[str, Any]], list[str]]:
    """Detect grid-like regions and optionally map OCR text into cell suggestions."""
    try:
        cv2, np, image = _load_cv(path)
    except Exception as exc:
        return [], [str(exc)]
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 31, 12)
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (max(15, width // 38), 1))
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(15, height // 34)))
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, hk)
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vk)
    grid = cv2.bitwise_or(horizontal, vertical)
    contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        x, y, rw, rh = cv2.boundingRect(contour)
        if rw < width * .16 or rh < height * .07 or rw * rh < width * height * .008:
            continue
        roi_h = horizontal[y:y + rh, x:x + rw]
        roi_v = vertical[y:y + rh, x:x + rw]
        hproj = (roi_h > 0).sum(axis=1)
        vproj = (roi_v > 0).sum(axis=0)
        hpos = _group_positions(np.where(hproj >= max(5, rw * .52))[0], tolerance=max(2, rh // 250))
        vpos = _group_positions(np.where(vproj >= max(5, rh * .52))[0], tolerance=max(2, rw // 250))
        if len(hpos) < 3 or len(vpos) < 3:
            continue
        # Ignore a large page frame with only sparse internal rules.
        row_count, col_count = len(hpos) - 1, len(vpos) - 1
        if row_count * col_count < 4:
            continue
        xs = [x + v for v in vpos]
        ys = [y + v for v in hpos]
        rows = [['' for _ in range(col_count)] for _ in range(row_count)]
        assigned = 0
        for item in ocr_items or []:
            bx = item.get('bbox_px', [])
            if len(bx) != 4:
                continue
            cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
            if not (x <= cx <= x + rw and y <= cy <= y + rh):
                continue
            ci = next((i for i in range(col_count) if xs[i] <= cx <= xs[i + 1]), None)
            ri = next((i for i in range(row_count) if ys[i] <= cy <= ys[i + 1]), None)
            if ci is not None and ri is not None:
                rows[ri][ci] = (rows[ri][ci] + ' ' + item.get('text', '')).strip()
                assigned += 1
        nonempty = sum(bool(cell.strip()) for row in rows for cell in row)
        candidates.append({'bbox_px': [x, y, x + rw, y + rh],
                           'bbox_norm': [round(x / width, 6), round(y / height, 6),
                                         round(rw / width, 6), round(rh / height, 6)],
                           'row_count': row_count, 'column_count': col_count,
                           'grid_x_px': xs, 'grid_y_px': ys,
                           'ocr_cells_filled': nonempty, 'ocr_items_assigned': assigned,
                           'suggested_rows': rows if nonempty else [],
                           'confidence': 0.72 if nonempty >= 3 else 0.52,
                           'source': 'opencv_grid_lines', 'needs_review': True})
    candidates.sort(key=lambda item: item['bbox_norm'][2] * item['bbox_norm'][3], reverse=True)
    kept = []
    for item in candidates:
        if any(_iou(item['bbox_norm'], old['bbox_norm']) > .68 for old in kept):
            continue
        kept.append(item)
        if len(kept) >= max_candidates:
            break
    return kept, []


def _line_fraction_in_ocr(a, b, ocr_items, samples=17):
    if not ocr_items:
        return 0.0
    hits = 0
    for i in range(samples):
        t = i / max(1, samples - 1)
        x = float(a[0] + (b[0] - a[0]) * t)
        y = float(a[1] + (b[1] - a[1]) * t)
        if any(len(item.get('bbox_px', [])) == 4 and
               item['bbox_px'][0] - 3 <= x <= item['bbox_px'][2] + 3 and
               item['bbox_px'][1] - 3 <= y <= item['bbox_px'][3] + 3 for item in ocr_items):
            hits += 1
    return hits / max(1, samples)


def _line_fraction_on_shape_border(a, b, shape_candidates, samples=17, pad=5):
    boxes = [item.get('bbox_px') for item in (shape_candidates or [])
             if item.get('shape') == 'rect' and len(item.get('bbox_px', [])) == 4]
    if not boxes:
        return 0.0
    hits = 0
    for i in range(samples):
        t = i / max(1, samples - 1)
        x = float(a[0] + (b[0] - a[0]) * t)
        y = float(a[1] + (b[1] - a[1]) * t)
        on_border = False
        for x1, y1, x2, y2 in boxes:
            if x1 - pad <= x <= x2 + pad and y1 - pad <= y <= y2 + pad:
                if min(abs(x - x1), abs(x - x2), abs(y - y1), abs(y - y2)) <= pad:
                    on_border = True
                    break
        if on_border:
            hits += 1
    return hits / max(1, samples)


def _line_fraction_inside_shapes(a, b, shape_candidates, samples=17):
    boxes = [item.get('bbox_px') for item in (shape_candidates or [])
             if item.get('shape') == 'rect' and len(item.get('bbox_px', [])) == 4]
    if not boxes:
        return 0.0
    hits = 0
    for i in range(samples):
        t = i / max(1, samples - 1)
        x = float(a[0] + (b[0] - a[0]) * t)
        y = float(a[1] + (b[1] - a[1]) * t)
        if any(x1 + 2 <= x <= x2 - 2 and y1 + 2 <= y <= y2 - 2
               for x1, y1, x2, y2 in boxes):
            hits += 1
    return hits / max(1, samples)


def _shape_overlaps_ocr(shape, ocr_items):
    x1, y1, x2, y2 = shape.get('bbox_px', [0, 0, 0, 0])
    area = max(1, (x2 - x1) * (y2 - y1))
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    for item in ocr_items or []:
        bx = item.get('bbox_px', [])
        if len(bx) != 4:
            continue
        ix = max(0, min(x2, bx[2]) - max(x1, bx[0]))
        iy = max(0, min(y2, bx[3]) - max(y1, bx[1]))
        if ix * iy / area > .45:
            return True
    return False

def _is_connector_shaft(a, b, ocr_items, shape_candidates):
    # Text baselines and card/table outlines are frequent Hough false positives.
    return (_line_fraction_in_ocr(a, b, ocr_items) < .22 and
            _line_fraction_on_shape_border(a, b, shape_candidates) < .55 and
            _line_fraction_inside_shapes(a, b, shape_candidates) < .28)


def detect_arrow_connectors(path: Path, max_connectors: int = 40,
                            ocr_items: list[dict[str, Any]] | None = None,
                            shape_candidates: list[dict[str, Any]] | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    """Pair Hough line segments with triangular arrowheads; output reviewable arrows."""
    try:
        cv2, np, image = _load_cv(path)
    except Exception as exc:
        return [], [str(exc)]
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 45, 135)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=10,
                            minLineLength=5, maxLineGap=8)
    if lines is None:
        return [], []
    # Filled or outlined triangle arrowheads.
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    triangles = []
    for contour in contours:
        area = abs(cv2.contourArea(contour))
        if area < max(12, width * height * .000008) or area > width * height * .003:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, .09 * perimeter, True)
        if len(approx) != 3:
            continue
        pts = approx.reshape(-1, 2).astype(float)
        # Tip is the vertex furthest from the opposite base midpoint.
        for tip_i in range(3):
            others = [i for i in range(3) if i != tip_i]
            base = (pts[others[0]] + pts[others[1]]) / 2
            tip = pts[tip_i]
            triangles.append((base, tip))
    tolerance = max(9.0, hypot(width, height) * .014)
    output = []
    for raw in lines.reshape(-1, 4):
        x1, y1, x2, y2 = [float(v) for v in raw]
        p1, p2 = np.array([x1, y1]), np.array([x2, y2])
        seg_len = float(np.linalg.norm(p2 - p1))
        if seg_len < max(22, min(width, height) * .035):
            continue
        if not _is_connector_shaft(p1, p2, ocr_items, shape_candidates):
            continue
        best = None
        for base, tip in triangles:
            tip_vec = tip - base
            tip_len = float(np.linalg.norm(tip_vec))
            if tip_len < 3:
                continue
            for line_end, other_end in ((p1, p2), (p2, p1)):
                dist = float(np.linalg.norm(line_end - base))
                if dist > tolerance:
                    continue
                flow_vec = base - other_end
                flow_len = float(np.linalg.norm(flow_vec))
                if flow_len < 5:
                    continue
                cosine = float(np.dot(flow_vec, tip_vec) / max(1e-6, flow_len * tip_len))
                if cosine < .62:
                    continue
                score = cosine - dist / tolerance * .15
                if best is None or score > best[0]:
                    best = (score, other_end, tip)
        if best is None:
            continue
        _, start, end = best
        pts_norm = [round(float(start[0]) / width, 6), round(float(start[1]) / height, 6),
                    round(float(end[0]) / width, 6), round(float(end[1]) / height, 6)]
        if hypot((pts_norm[2] - pts_norm[0]) * width, (pts_norm[3] - pts_norm[1]) * height) < 12:
            continue
        if any(hypot((old['points_norm'][0] - pts_norm[0]) * width,
                     (old['points_norm'][1] - pts_norm[1]) * height) < 12 and
               hypot((old['points_norm'][2] - pts_norm[2]) * width,
                     (old['points_norm'][3] - pts_norm[3]) * height) < 18 for old in output):
            continue
        output.append({'points_px': [round(float(start[0])), round(float(start[1])),
                                     round(float(end[0])), round(float(end[1]))],
                       'points_norm': pts_norm, 'arrow': 'end', 'confidence': .78,
                       'source': 'hough_line_plus_triangle_head', 'needs_review': True})
        if len(output) >= max_connectors:
            break
    if len(output) >= max_connectors:
        return output, []
    # Fallback: detect an open V-shaped arrowhead from two short Hough segments.
    # The previous all-pairs implementation was quadratic in every short Hough
    # segment. Dense slide text can produce thousands of such segments, so use
    # endpoint spatial hashing and only inspect geometrically adjacent pairs.
    segments = []
    for raw in lines.reshape(-1, 4):
        a = np.array([float(raw[0]), float(raw[1])])
        b = np.array([float(raw[2]), float(raw[3])])
        length = float(np.linalg.norm(b - a))
        if length >= 5:
            segments.append((a, b, length))

    short_max = min(width, height) * .10
    join_tol = max(5.0, hypot(width, height) * .006)
    base_tol = max(10.0, hypot(width, height) * .014)
    long_segments = [seg for seg in segments
                     if seg[2] >= max(30, min(width, height) * .07)
                     and _is_connector_shaft(seg[0], seg[1], ocr_items, shape_candidates)]
    short_segments = [seg for seg in segments if 5 <= seg[2] <= short_max]

    # Index long-shaft endpoints so V heads are only retained when they can
    # plausibly attach to a connector shaft.
    shaft_endpoint_grid = defaultdict(list)
    for seg_index, (a, b, _length) in enumerate(long_segments):
        shaft_endpoint_grid[(int(a[0] // base_tol), int(a[1] // base_tol))].append((seg_index, a, b))
        shaft_endpoint_grid[(int(b[0] // base_tol), int(b[1] // base_tol))].append((seg_index, b, a))

    # Build candidate short-segment pairs from nearby endpoints. The cap is a
    # safety valve for unusually dense diagrams; truncation is reported below.
    endpoint_grid = defaultdict(list)
    segment_pairs = set()
    max_pair_candidates = 50000
    max_bucket_items = 64
    pairing_truncated = False
    for seg_index, (a, b, length) in enumerate(short_segments):
        for endpoint in (a, b):
            cell_x, cell_y = int(endpoint[0] // join_tol), int(endpoint[1] // join_tol)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nearby = endpoint_grid.get((cell_x + dx, cell_y + dy), ())
                    for other_index, other_endpoint in nearby:
                        if other_index == seg_index:
                            continue
                        if float(np.linalg.norm(endpoint - other_endpoint)) > join_tol:
                            continue
                        other_length = short_segments[other_index][2]
                        if max(length, other_length) / max(1e-6, min(length, other_length)) > 1.8:
                            continue
                        segment_pairs.add((min(seg_index, other_index), max(seg_index, other_index)))
                        if len(segment_pairs) >= max_pair_candidates:
                            pairing_truncated = True
                            break
                    if pairing_truncated:
                        break
                if pairing_truncated:
                    break
            bucket = endpoint_grid[(cell_x, cell_y)]
            if len(bucket) < max_bucket_items:
                bucket.append((seg_index, endpoint))
            if pairing_truncated:
                break
        if pairing_truncated:
            break

    # Deduplicate V heads with a second spatial index. Each retained head also
    # carries its nearby shaft endpoints, avoiding a head × all-shafts scan.
    arrow_heads = []
    head_grid = defaultdict(list)
    head_cell = max(8.0, min(join_tol, 12.0))
    for first_index, second_index in sorted(segment_pairs):
        a1, b1, _l1 = short_segments[first_index]
        a2, b2, _l2 = short_segments[second_index]
        for tip1, base1 in ((a1, b1), (b1, a1)):
            for tip2, base2 in ((a2, b2), (b2, a2)):
                if float(np.linalg.norm(tip1 - tip2)) > join_tol:
                    continue
                tip = (tip1 + tip2) / 2
                base_mid = (base1 + base2) / 2
                v1, v2 = tip - base1, tip - base2
                len1, len2 = float(np.linalg.norm(v1)), float(np.linalg.norm(v2))
                if min(len1, len2) < 4 or max(len1, len2) / max(1e-6, min(len1, len2)) > 1.65:
                    continue
                spread = float(np.degrees(np.arccos(np.clip(np.dot(v1, v2) /
                                                              max(1e-6, len1 * len2), -1, 1))))
                if not 22 <= spread <= 100:
                    continue

                # Find plausible shaft endpoints close to the V base midpoint.
                sx, sy = int(base_mid[0] // base_tol), int(base_mid[1] // base_tol)
                nearby_shafts = []
                seen_shafts = set()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for shaft_index, endpoint, origin in shaft_endpoint_grid.get((sx + dx, sy + dy), ()):
                            if shaft_index in seen_shafts:
                                continue
                            if float(np.linalg.norm(base_mid - endpoint)) <= base_tol:
                                nearby_shafts.append((shaft_index, endpoint, origin))
                                seen_shafts.add(shaft_index)
                if not nearby_shafts:
                    continue

                hx, hy = int(tip[0] // head_cell), int(tip[1] // head_cell)
                duplicate = False
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for old_tip, old_base in head_grid.get((hx + dx, hy + dy), ()):
                            if np.linalg.norm(tip - old_tip) < 8 and np.linalg.norm(base_mid - old_base) < 10:
                                duplicate = True
                                break
                        if duplicate:
                            break
                    if duplicate:
                        break
                if duplicate:
                    continue
                head_grid[(hx, hy)].append((tip, base_mid))
                arrow_heads.append((tip, base_mid, v1, v2, nearby_shafts))

    for tip, base_mid, v1, v2, nearby_shafts in arrow_heads:
        best = None
        for _shaft_index, endpoint, origin in nearby_shafts:
            flow = base_mid - origin
            flow_len = max(1e-6, float(np.linalg.norm(flow)))
            len1, len2 = float(np.linalg.norm(v1)), float(np.linalg.norm(v2))
            cos1 = float(np.dot(flow, v1) / (flow_len * max(1e-6, len1)))
            cos2 = float(np.dot(flow, v2) / (flow_len * max(1e-6, len2)))
            cross1 = float(flow[0] * v1[1] - flow[1] * v1[0])
            cross2 = float(flow[0] * v2[1] - flow[1] * v2[0])
            if min(cos1, cos2) < .38 or cross1 * cross2 >= 0:
                continue
            head = tip - base_mid
            cosine = float(np.dot(flow, head) /
                           max(1e-6, np.linalg.norm(flow) * np.linalg.norm(head)))
            if cosine < .72:
                continue
            score = cosine - float(np.linalg.norm(base_mid - endpoint)) / base_tol * .15
            if best is None or score > best[0]:
                best = (score, origin, tip)
        if best is None:
            continue
        _, origin, end = best
        pts_norm = [round(float(origin[0]) / width, 6), round(float(origin[1]) / height, 6),
                    round(float(end[0]) / width, 6), round(float(end[1]) / height, 6)]
        if any(hypot((old['points_norm'][0] - pts_norm[0]) * width,
                     (old['points_norm'][1] - pts_norm[1]) * height) < 14 and
               hypot((old['points_norm'][2] - pts_norm[2]) * width,
                     (old['points_norm'][3] - pts_norm[3]) * height) < 20 for old in output):
            continue
        output.append({'points_px': [round(float(origin[0])), round(float(origin[1])),
                                     round(float(end[0])), round(float(end[1]))],
                       'points_norm': pts_norm, 'arrow': 'end', 'confidence': .74,
                       'source': 'hough_shaft_plus_v_head', 'needs_review': True})
        if len(output) >= max_connectors:
            break

    if pairing_truncated:
        return output, ['开放式 V 形箭头候选达到配对上限，已截断部分候选；请人工检查叠加图。']
    return output, []


def _overlap_ratio(box_a, box_b):
    ax, ay, aw, ah = box_a; bx, by, bw, bh = box_b
    inter = max(0, min(ax + aw, bx + bw) - max(ax, bx)) * max(0, min(ay + ah, by + bh) - max(ay, by))
    return inter / max(1, aw * ah)


def _nearby_text(candidate, ocr_items, width, height):
    x1, y1, x2, y2 = candidate['bbox_px']
    x, y, w, h = x1, y1, x2 - x1, y2 - y1
    cx, cy = x + w / 2, y + h / 2
    ranked = []
    for item in ocr_items:
        bx = item.get('bbox_px', [])
        if len(bx) != 4:
            continue
        tx, ty, tw, th = bx[0], bx[1], bx[2] - bx[0], bx[3] - bx[1]
        tcx, tcy = tx + tw / 2, ty + th / 2
        dx, dy = tcx - cx, tcy - cy
        # Favor a label to the right of the icon, then below/above in the same card.
        if dx >= -w * .25 and abs(dy) <= max(h * .85, height * .055) and dx <= width * .22:
            score = hypot(max(0, dx), dy) + (0 if dx >= 0 else w * .5)
            ranked.append((score, item.get('text', '')))
        elif abs(dx) <= max(w * 2.0, width * .06) and abs(dy) <= height * .06:
            ranked.append((hypot(dx, dy) + w, item.get('text', '')))
    return min(ranked, default=(0, ''))[1]


def _suggest_icons(context: str, icon_library, limit: int = 5):
    if not context or icon_library is None:
        return []
    seen = {}
    by_id = {item['id']: item for item in getattr(icon_library, 'items', [])}
    # Direct lexical overlap against the library's Chinese names/keywords/aliases
    # is useful for multi-character OCR labels that are not an exact index key.
    for item in getattr(icon_library, 'items', []):
        terms = [item.get('name_zh', '')] + list(item.get('keywords_zh') or []) + list(item.get('aliases_zh') or [])
        matched = [term for term in terms if term and len(term) >= 2 and (term in context or context in term)]
        if matched:
            specificity = max(len(term) for term in matched)
            seen[item['id']] = max(seen.get(item['id'], 0), 65 + min(25, specificity * 5) +
                                   min(10, float(item.get('selection_score_total', 0)) / 10))
    tokens = [token for token in re.findall(r'[\u4e00-\u9fff]{2,8}|[A-Za-z][A-Za-z0-9_-]*', context) if len(token) >= 2]
    queries = list(dict.fromkeys([context.strip()] + tokens))
    for query in queries[:8]:
        try:
            for rank, item in enumerate(icon_library.search(query, limit=limit), 1):
                score = 58 - (rank - 1) * 7
                score += min(10, float(item.get('selection_score_total', 0)) / 10)
                seen[item['id']] = max(seen.get(item['id'], 0), score)
        except Exception:
            continue
    ordered = sorted(seen, key=lambda key: (-seen[key], by_id.get(key, {}).get('priority', 'P9')))
    return [{'icon_id': key, 'name_zh': by_id[key].get('name_zh', key),
             'category': by_id[key].get('category', ''),
             'relative_path': by_id[key].get('relative_path', ''),
             'context_match_score': round(seen[key], 2)} for key in ordered[:limit] if key in by_id]


def detect_icon_candidates(path: Path, ocr_items: list[dict[str, Any]] | None = None,
                           icon_library=None, max_candidates: int = 60) -> tuple[list[dict[str, Any]], list[str]]:
    """Find compact non-text pictogram-like regions and suggest SVGs from nearby labels.

    Matching is contextual (OCR label -> semantic index), not a claim of pixel-level
    image recognition. Suggestions must be confirmed before adding icon_id to a spec.
    """
    try:
        cv2, np, image = _load_cv(path)
    except Exception as exc:
        return [], [str(exc)]
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Remove very light background and merge small strokes into icon-sized components.
    _, binary = cv2.threshold(gray, 218, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    merged = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(merged, 8)
    min_side = max(12, int(min(width, height) * .014))
    max_side = int(min(width, height) * .105)
    items = []
    for idx in range(1, count):
        x, y, w, h, area = [int(v) for v in stats[idx]]
        if w < min_side or h < min_side or w > max_side or h > max_side:
            continue
        aspect = w / max(1, h)
        if not .48 <= aspect <= 2.05 or area < 10:
            continue
        box = [x, y, w, h]
        overlaps_text = False
        for item in ocr_items or []:
            b = item.get('bbox_px', [])
            if len(b) != 4 or _overlap_ratio(box, (b[0], b[1], b[2]-b[0], b[3]-b[1])) <= .18:
                continue
            text = str(item.get('text', '')).strip()
            words = re.findall(r'[A-Za-z]+|[0-9]+|[\u4e00-\u9fff]+', text)
            # OCR sometimes merges a circular/compact icon into a leading glyph
            # (e.g. "Q Factory"). Preserve a compact left-side component so its
            # semantic label can still retrieve a library SVG candidate.
            merged_icon_prefix = (len(words) >= 2 and len(words[0]) == 1 and
                                  x + w / 2 <= b[0] + (b[2] - b[0]) * .42 and
                                  y + h / 2 >= b[1] - 3 and y + h / 2 <= b[3] + 3)
            if not merged_icon_prefix:
                overlaps_text = True
                break
        if overlaps_text:
            continue
        # Ignore long rules and tiny text-like flecks.
        density = area / max(1, w * h)
        if density < .025 or density > .92:
            continue
        norm = [round(x / width, 6), round(y / height, 6), round(w / width, 6), round(h / height, 6)]
        candidate = {'bbox_px': [x, y, x + w, y + h], 'bbox_norm': norm,
                     'aspect_ratio': round(aspect, 3), 'pixel_density': round(density, 3),
                     'confidence': .38, 'source': 'compact_visual_component',
                     'needs_review': True}
        candidate['nearby_text'] = _nearby_text(candidate, ocr_items or [], width, height)
        candidate['icon_suggestions'] = _suggest_icons(candidate['nearby_text'], icon_library)
        items.append(candidate)
    # Suppress fragmented strokes around one icon; retain the larger coherent region.
    items.sort(key=lambda item: item['bbox_norm'][2] * item['bbox_norm'][3], reverse=True)
    kept = []
    for item in items:
        if any(_iou(item['bbox_norm'], old['bbox_norm']) > .72 for old in kept):
            continue
        kept.append(item)
        if len(kept) >= max_candidates:
            break
    return kept, []


def infer_layout_hypotheses(shape_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Identify repeated, similarly sized boxes aligned in a row/column."""
    boxes = [x for x in shape_candidates if x.get('shape') == 'rect' and x.get('bbox_norm', [0,0,0,0])[2] < .48]
    hypotheses = []
    used = set()
    for i, a in enumerate(boxes):
        if i in used:
            continue
        ax, ay, aw, ah = a['bbox_norm']
        group = [i]
        for j in range(i + 1, len(boxes)):
            bx, by, bw, bh = boxes[j]['bbox_norm']
            same_size = abs(aw - bw) <= max(.025, aw * .16) and abs(ah - bh) <= max(.025, ah * .2)
            same_row = abs((ay + ah / 2) - (by + bh / 2)) <= max(.025, ah * .25)
            same_col = abs((ax + aw / 2) - (bx + bw / 2)) <= max(.025, aw * .25)
            if same_size and (same_row or same_col):
                group.append(j)
        if len(group) >= 3:
            used.update(group)
            hypotheses.append({'layout': 'repeated_card_row' if abs(boxes[group[0]]['bbox_norm'][1] - boxes[group[1]]['bbox_norm'][1]) < .04 else 'repeated_card_column',
                               'candidate_indices': group, 'count': len(group),
                               'confidence': .46, 'needs_review': True})
    return hypotheses


def analyze_structure(path: Path, ocr_items: list[dict[str, Any]] | None = None,
                       icon_library=None) -> dict[str, Any]:
    """Run geometry, table, arrow, icon-context and repeated-layout proposals."""
    shapes, w1 = detect_shape_candidates(path)
    # Contours inside OCR text boxes are usually glyphs, not PowerPoint shapes.
    shapes = [shape for shape in shapes if not _shape_overlaps_ocr(shape, ocr_items)]
    tables, w2 = detect_table_candidates(path, ocr_items)
    arrows, w3 = detect_arrow_connectors(path, ocr_items=ocr_items, shape_candidates=shapes)
    if ocr_items:
        icons, w4 = detect_icon_candidates(path, ocr_items, icon_library)
    else:
        icons, w4 = [], ['没有 OCR 文本框，跳过邻近标签驱动的图标语义候选定位。']
    # Grid cells are represented by one table candidate, not dozens of nested
    # rectangle candidates. Keep non-table shape candidates for downstream use.
    filtered_shapes = []
    for shape in shapes:
        sx, sy, sw, sh = shape['bbox_norm']
        scx, scy = sx + sw / 2, sy + sh / 2
        inside_table = any(tx <= scx <= tx + tw and ty <= scy <= ty + th
                           for tx, ty, tw, th in [table['bbox_norm'] for table in tables])
        if not inside_table:
            filtered_shapes.append(shape)
    layouts = infer_layout_hypotheses(filtered_shapes)
    return {'shape_candidates': filtered_shapes, 'table_candidates': tables,
            'connector_candidates': arrows, 'icon_candidates': icons,
            'layout_hypotheses': layouts,
            'warnings': list(dict.fromkeys(w1 + w2 + w3 + w4)),
            'method_notes': [
                '图形类型来自轮廓几何，不代表其业务语义已经确认。',
                '箭头由 Hough 线段与三角形箭头头部配对提出，端点和方向必须复核。',
                '表格由横纵网格线检测，OCR 单元格映射仅为建议。',
                '图标候选由紧凑视觉区域定位；SVG 匹配基于邻近 OCR 标签的语义检索，不是像素级图标分类。',
                '重复卡片/布局推断仅依据几何对齐和尺寸相似度。'
            ]}
