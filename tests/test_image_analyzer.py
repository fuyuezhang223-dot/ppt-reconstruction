"""Pure-function tests for OCR-assisted image analysis; no OCR model required."""
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from jsonschema import validate
from core.image_analyzer import OCRItem, make_draft_spec, collect_images, analyze_one, analyze_batch
from core.ppt_builder import Builder

ROOT = Path(__file__).resolve().parents[1]
TOKENS = json.loads((ROOT / 'config/design_tokens.json').read_text(encoding='utf-8'))


class ImageAnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='ppt_v43_')
        self.root = Path(self.tmp.name)
        self.image = self.root / '参考页.png'
        Image.new('RGB', (1600, 900), 'white').save(self.image)

    def tearDown(self):
        self.tmp.cleanup()

    def test_ocr_box_normalization_clips_to_image(self):
        item = OCRItem('测试文字', [-5, 10, 400, 1000], .91, 'mock')
        normalized = item.normalized(1600, 900)
        self.assertEqual(normalized['bbox_px'], [0, 10, 400, 900])
        self.assertEqual(normalized['bbox_norm'], [0.0, 0.011111, 0.25, 0.988889])

    def test_draft_spec_uses_native_text_and_marks_review(self):
        info = {'width': 1600, 'height': 900, 'aspect_ratio': 16/9, 'background_hint': '#FFFFFF'}
        items = [
            {'text': '标题文字', 'bbox_px': [100, 80, 800, 150],
             'bbox_norm': [.0625, .088889, .4375, .077778], 'confidence': .96, 'engine': 'mock'},
            {'text': '低置信度内容', 'bbox_px': [100, 300, 500, 340],
             'bbox_norm': [.0625, .333333, .25, .044444], 'confidence': .42, 'engine': 'mock'}
        ]
        spec = make_draft_spec(self.image, info, items, [], min_confidence=.75)
        self.assertEqual(spec['route'], 'strict_reconstruction')
        self.assertEqual(len(spec['pages'][0]['elements']), 2)
        self.assertEqual(spec['pages'][0]['elements'][0]['type'], 'text')
        self.assertFalse(spec['pages'][0]['elements'][0]['needs_review'])
        self.assertTrue(spec['pages'][0]['elements'][1]['needs_review'])
        schema = json.loads((ROOT / 'schemas/page_spec.schema.json').read_text(encoding='utf-8'))
        validate(spec, schema)

    def test_builder_honors_slide_size_from_spec(self):
        spec = {'route': 'strict_reconstruction', 'slide_size_in': [10, 5.625],
                'pages': [{'page_id': 's1', 'elements': [
                    {'type': 'text', 'id': 't1', 'bbox_norm': [.1, .1, .5, .2], 'text': '测试', 'font_size': 18}
                ]}]}
        out = self.root / 'draft.pptx'
        builder = Builder(TOKENS, self.root)
        builder.build(spec, out)
        from pptx import Presentation
        prs = Presentation(out)
        self.assertAlmostEqual(prs.slide_width / 914400, 10, places=3)
        self.assertAlmostEqual(prs.slide_height / 914400, 5.625, places=3)

    def test_collect_images_sorts_folder(self):
        (self.root / 'b.png').write_bytes(self.image.read_bytes())
        (self.root / 'a.png').write_bytes(self.image.read_bytes())
        self.assertEqual([p.name for p in collect_images(self.root)], ['a.png', 'b.png', '参考页.png'])

    def test_analyze_one_without_ocr_is_explicitly_review_required(self):
        report, draft, items, warnings = analyze_one(
            self.image, engine='none', detect_shapes=False, page_height_in=8.0
        )
        self.assertEqual(report['ocr']['engine'], 'none')
        self.assertEqual(items, [])
        self.assertEqual(draft['analysis_status'], 'REVIEW_REQUIRED')
        self.assertTrue(any('未执行 OCR' in x for x in warnings))

    def test_collect_images_excludes_output_directory(self):
        output = self.root / 'outputs'
        output.mkdir()
        (output / 'overlay_001.png').write_bytes(self.image.read_bytes())
        found = collect_images(self.root, exclude_dir=output)
        self.assertEqual([p.name for p in found], ['参考页.png'])

    def test_batch_writes_reports_and_multpage_draft(self):
        (self.root / '02.png').write_bytes(self.image.read_bytes())
        output = self.root / 'analysis'
        summary = analyze_batch(self.root, output, engine='none', detect_shapes=False)
        self.assertEqual(summary['image_count'], 2)
        spec = json.loads((output / 'draft_spec.json').read_text(encoding='utf-8'))
        self.assertEqual(len(spec['pages']), 2)
        schema = json.loads((ROOT / 'schemas/page_spec.schema.json').read_text(encoding='utf-8'))
        validate(spec, schema)
        self.assertTrue((output / 'analysis_001.json').is_file())
        self.assertTrue((output / 'overlay_002.png').is_file())


if __name__ == '__main__':
    unittest.main()
