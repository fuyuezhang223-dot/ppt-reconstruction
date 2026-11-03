"""Synthetic tests for v4.4 visual-structure proposals (not an accuracy benchmark)."""
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from jsonschema import validate
from pptx import Presentation

from core.icon_library import IconLibrary
from core.structure_analyzer import analyze_structure, detect_arrow_connectors
from core.image_analyzer import make_draft_spec, analyze_one, draw_overlay
from core.ppt_builder import Builder

ROOT = Path(__file__).resolve().parents[1]
TOKENS = json.loads((ROOT / 'config/design_tokens.json').read_text(encoding='utf-8'))


class StructureAnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='ppt_v44_')
        self.root = Path(self.tmp.name)
        self.image = self.root / 'synthetic_structure.png'
        im = Image.new('RGB', (1200, 675), 'white')
        d = ImageDraw.Draw(im)
        # Three repeated process cards.
        for x in (120, 420, 720):
            d.rounded_rectangle((x, 100, x + 190, 220), radius=12,
                                outline='#333333', width=4, fill='#F4F7FA')
        # Three distinct geometric types.
        d.ellipse((980, 90, 1080, 190), outline='#222222', width=4)
        d.polygon([(1030, 260), (1080, 310), (1030, 360), (980, 310)],
                  outline='#222222', fill='white', width=4)
        d.polygon([(1040, 410), (1090, 500), (990, 500)],
                  outline='#222222', fill='white', width=4)
        # Right-pointing line arrow.
        d.line((310, 160, 390, 160), fill='#222222', width=4)
        d.polygon([(405, 160), (386, 148), (386, 172)], fill='#222222')
        # 3 x 3 table grid.
        x0, y0, x1, y1 = 100, 400, 700, 610
        for x in (x0, 300, 500, x1):
            d.line((x, y0, x, y1), fill='#222222', width=3)
        for y in (y0, 470, 540, y1):
            d.line((x0, y, x1, y), fill='#222222', width=3)
        # Compact check pictogram adjacent to its label.
        d.ellipse((820, 420, 860, 460), outline='#222222', width=3)
        d.line((830, 440, 840, 450, 853, 430), fill='#222222', width=3)
        im.save(self.image)
        self.ocr = [
            {'text': '工厂', 'bbox_px': [870, 420, 930, 450],
             'bbox_norm': [.725, .622, .05, .044], 'confidence': .96},
            {'text': '表头A', 'bbox_px': [150, 420, 230, 445],
             'bbox_norm': [.125, .622, .067, .037], 'confidence': .94},
            {'text': '表头B', 'bbox_px': [350, 420, 430, 445],
             'bbox_norm': [.292, .622, .067, .037], 'confidence': .94},
            {'text': '表头C', 'bbox_px': [550, 420, 630, 445],
             'bbox_norm': [.458, .622, .067, .037], 'confidence': .94},
        ]
        self.structure = analyze_structure(self.image, self.ocr, IconLibrary())

    def tearDown(self):
        self.tmp.cleanup()

    def test_detects_distinct_geometry_types(self):
        kinds = {x['shape'] for x in self.structure['shape_candidates']}
        self.assertIn('ellipse', kinds)
        self.assertIn('diamond', kinds)
        self.assertIn('triangle', kinds)
        self.assertIn('rect', kinds)

    def test_detects_table_grid_and_maps_ocr_cells(self):
        self.assertTrue(self.structure['table_candidates'])
        table = self.structure['table_candidates'][0]
        self.assertEqual((table['row_count'], table['column_count']), (3, 3))
        self.assertGreaterEqual(table['ocr_cells_filled'], 3)
        self.assertEqual(table['suggested_rows'][0], ['表头A', '表头B', '表头C'])

    def test_detects_right_pointing_arrow_without_rectangle_corner_false_positive(self):
        arrows = self.structure['connector_candidates']
        self.assertEqual(len(arrows), 1, arrows)
        x1, y1, x2, y2 = arrows[0]['points_norm']
        self.assertGreater(x2, x1)
        self.assertLess(abs(y2 - y1), .02)

    def test_ignores_text_baselines_and_card_borders_as_arrows(self):
        image = self.root / 'no_arrow_page.png'
        im = Image.new('RGB', (1000, 560), 'white')
        d = ImageDraw.Draw(im)
        d.text((95, 70), 'Editable PPT Workflow v4.4', fill='#1F3B5B')
        d.rounded_rectangle((70, 210, 610, 450), radius=24,
                            outline='#7A9DBD', width=5, fill='#E5EEF6')
        d.text((115, 300), 'OCR-assisted draft', fill='#243347')
        im.save(image)
        ocr = [
            {'text': 'Editable PPT Workflow v4.4', 'bbox_px': [90, 60, 610, 110]},
            {'text': 'OCR-assisted draft', 'bbox_px': [110, 290, 420, 345]},
        ]
        result = analyze_structure(image, ocr, IconLibrary())
        self.assertEqual(result['connector_candidates'], [])


    def test_detects_open_v_arrow_with_spatial_pairing(self):
        image = self.root / 'open_v_arrow.png'
        im = Image.new('RGB', (900, 500), 'white')
        d = ImageDraw.Draw(im)
        d.line((180, 250, 665, 250), fill='#222222', width=4)
        d.line((690, 250, 665, 228), fill='#222222', width=4)
        d.line((690, 250, 665, 272), fill='#222222', width=4)
        im.save(image)
        arrows, warnings = detect_arrow_connectors(image, max_connectors=10,
                                                   ocr_items=[], shape_candidates=[])
        self.assertFalse(warnings, warnings)
        self.assertTrue(arrows, 'expected an open V-shaped arrow candidate')
        self.assertTrue(any(item['points_norm'][2] > item['points_norm'][0] for item in arrows))

    def test_dense_real_slide_respects_arrow_candidate_limit(self):
        image = ROOT / 'examples/real_cases/eam_6pages/references/slide_205.png'
        if not image.exists():
            self.skipTest('real EAM reference slide is not included')
        arrows, _warnings = detect_arrow_connectors(image, max_connectors=8,
                                                     ocr_items=[], shape_candidates=[])
        self.assertLessEqual(len(arrows), 8)

    def test_icon_candidate_gets_contextual_svg_suggestions(self):
        icons = self.structure['icon_candidates']
        self.assertEqual(len(icons), 1, icons)
        self.assertEqual(icons[0]['nearby_text'], '工厂')
        ids = [x['icon_id'] for x in icons[0]['icon_suggestions']]
        self.assertIn('MFG-001', ids)
        self.assertTrue(all(x['relative_path'].endswith('.svg') for x in icons[0]['icon_suggestions']))
        # OCR can merge a circular pictogram into the first glyph of its label.
        merged = [{'text': 'Q Factory', 'bbox_px': [815, 415, 970, 465],
                   'bbox_norm': [.679, .615, .129, .074], 'confidence': .81}]
        merged_result = analyze_structure(self.image, merged, IconLibrary())
        self.assertTrue(merged_result['icon_candidates'])
        merged_ids = [x['icon_id'] for x in merged_result['icon_candidates'][0]['icon_suggestions']]
        self.assertIn('MFG-001', merged_ids)

    def test_repeated_cards_are_grouped_but_table_cells_are_not(self):
        layouts = self.structure['layout_hypotheses']
        self.assertTrue(any(x['count'] == 3 and x['layout'] == 'repeated_card_row' for x in layouts))
        self.assertFalse(any(x['count'] >= 4 for x in layouts))

    def test_draft_spec_contains_reviewable_native_candidates(self):
        info = {'width': 1200, 'height': 675, 'aspect_ratio': 16/9, 'background_hint': '#FFFFFF'}
        spec = make_draft_spec(self.image, info, self.ocr,
                               self.structure.get('shape_candidates', [])[:0],
                               min_confidence=.75, structure=self.structure)
        schema = json.loads((ROOT / 'schemas/page_spec.schema.json').read_text(encoding='utf-8'))
        validate(spec, schema)
        elems = spec['pages'][0]['elements']
        self.assertTrue(any(e['type'] == 'connector' for e in elems))
        self.assertTrue(any(e['type'] == 'table' for e in elems))
        self.assertTrue(any(e.get('shape') == 'diamond' for e in elems))
        self.assertEqual(spec['analysis_status'], 'REVIEW_REQUIRED')

    def test_image_analyzer_integrates_structure_and_review_overlay(self):
        report, draft, ocr_items, warnings = analyze_one(
            self.image, engine='none', detect_shapes=True, page_height_in=7.5
        )
        self.assertIn('structure', report)
        self.assertTrue(report['structure']['connector_candidates'])
        self.assertTrue(report['structure']['table_candidates'])
        self.assertEqual(draft['analysis_status'], 'REVIEW_REQUIRED')
        overlay = self.root / 'review_overlay.png'
        draw_overlay(self.image, ocr_items, overlay, structure=report['structure'])
        self.assertTrue(overlay.is_file())
        self.assertGreater(overlay.stat().st_size, 1000)

    def test_candidate_draft_builds_as_editable_powerpoint_objects(self):
        info = {'width': 1200, 'height': 675, 'aspect_ratio': 16/9, 'background_hint': '#FFFFFF'}
        spec = make_draft_spec(self.image, info, self.ocr, [], min_confidence=.75,
                               structure=self.structure)
        output = self.root / 'structure_draft.pptx'
        Builder(TOKENS, ROOT).build(spec, output)
        slide = Presentation(output).slides[0]
        self.assertTrue(any(shape.has_table for shape in slide.shapes))
        self.assertTrue(any(shape.shape_type == 9 for shape in slide.shapes))
        self.assertGreaterEqual(sum(shape.shape_type == 1 for shape in slide.shapes), 2)


if __name__ == '__main__':
    unittest.main()
