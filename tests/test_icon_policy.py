"""Prevent regression to screenshot-cropped standard icons."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'examples/real_cases/eam_6pages'
class IconPolicyTests(unittest.TestCase):
    def test_no_cropped_icons_in_release(self):
        self.assertFalse((CASE/'assets/icons').exists())
        self.assertFalse((CASE/'prepare_assets.py').exists())
    def test_every_configured_icon_exists_in_svg_library(self):
        from core.icon_library import IconLibrary
        lib=IconLibrary()
        data=json.loads((CASE/'pages.json').read_text(encoding='utf8'))
        for page in data['pages']:
            for field in ('step_icons','pre_icons','post_icons'):
                for icon in page.get(field,[]):
                    with self.subTest(page=page['page_num'],icon=icon):
                        path,item=lib.path(icon)
                        self.assertEqual(path.suffix,'.svg')
    def test_source_cropped_icon_path_rejected(self):
        from core.eam_course_template import EAMRenderer
        r=EAMRenderer(CASE); slide=r.ppt.slides.add_slide(r.ppt.slide_layouts[6])
        with self.assertRaises(ValueError):
            r.photo(slide,'s','assets/icons/210_step_1.png',0,0,50,50)
    def test_generic_builder_rejects_icon_as_image(self):
        from core.ppt_builder import Builder
        from pptx.util import Inches
        b=Builder({},CASE); slide=b.ppt.slides.add_slide(b.ppt.slide_layouts[6])
        with self.assertRaises(ValueError):
            b._image(slide,{'src':'assets/icons/x.png'},(0,0,Inches(1),Inches(1)))
if __name__=='__main__':unittest.main()
