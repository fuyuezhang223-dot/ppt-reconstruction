"""Synthetic regression/negative tests; NOT calibrated to user reference images."""
import copy,json,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
from pptx import Presentation
from pptx.oxml.xmlchemy import OxmlElement
from core.component_registry import expand_spec,COMPONENTS
from core.ppt_builder import Builder
from core.reference_compare import compare_structure,compare_visual
from core.geometry import resolve_connectors
from core.repair_engine import detect_spec_bounds, repair_with_regression

ROOT=Path(__file__).resolve().parents[1]
TOKENS=json.loads((ROOT/'config/design_tokens.json').read_text())
POLICY=json.loads((ROOT/'config/repair_policy.json').read_text())

class V42Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='ppt_v42_')
        self.dir=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def spec(self,elements):return {'route':'strict_reconstruction','pages':[{'page_id':'s1','elements':elements}]}

    def test_eight_component_names(self):
        self.assertEqual(len(COMPONENTS),8)
        self.assertIn('horizontal_flow',COMPONENTS)
    def test_all_components_expand(self):
        e=[{'component':'title_block','id':'head','bbox_norm':[.05,.04,.8,.12],'title':'标题'},
           {'component':'horizontal_flow','id':'flow','bbox_norm':[.06,.2,.85,.16],'nodes':[{'id':'a','title':'一'},{'id':'b','title':'二'}]},
           {'component':'flow_node','id':'node','bbox_norm':[.1,.42,.19,.13],'title':'三'},
           {'component':'icon_card','id':'icon','bbox_norm':[.32,.43,.21,.18],'icon_id':'MFG-001','title':'四'},
           {'component':'table_block','id':'tbl','bbox_norm':[.56,.42,.38,.17],'rows':[['A','B'],['1','2']]},
           {'component':'image_text','id':'img','bbox_norm':[.05,.64,.38,.25],
            'src':str(ROOT/'examples/assets/sample_workshop.png'),'title':'设备','text':'处理'},
           {'component':'timeline','id':'time','bbox_norm':[.49,.64,.46,.14],
            'items':[{'label':'计划'},{'label':'完成'}]},
           {'component':'comparison_matrix','id':'matrix','bbox_norm':[.45,.80,.49,.17],
            'columns':[{'title':'A','text':'规则'},{'title':'B','text':'代码'}]}]
        obj=expand_spec(self.spec(e),TOKENS)['pages'][0]['elements']
        self.assertTrue(len(obj)>len(e))
        self.assertEqual(len({x['id'] for x in obj}),len(obj))
        self.assertTrue(all(x.get('component_parent') for x in obj))
    def test_flow_auto_anchors_follow_moved_node(self):
        e=[{'type':'shape','id':'a','bbox_norm':[.1,.3,.2,.2]},
           {'type':'shape','id':'b','bbox_norm':[.55,.3,.2,.2]},
           {'type':'connector','id':'edge','from_id':'a','to_id':'b'}]
        original=resolve_connectors(e)[2]['points_norm']
        e[1]['bbox_norm'][0]=.65
        changed=resolve_connectors(e)[2]['points_norm']
        self.assertNotEqual(original,changed)
        self.assertAlmostEqual(changed[2],.65)
    def test_stable_native_object_names_and_text(self):
        sp=self.spec([{'type':'text','id':'welcome','bbox_norm':[.1,.1,.6,.13], 'text':'原生中文','font_size':18}])
        ppt=self.dir/'t.pptx';Builder(TOKENS,self.dir).build(sp,ppt)
        sh=Presentation(ppt).slides[0].shapes[0]
        self.assertEqual(sh.name,'welcome')
        self.assertEqual(sh.text,'原生中文')
        self.assertEqual(compare_structure(sp,ppt,TOKENS)['P0'],0)
    def test_missing_native_object_detection(self):
        sp=self.spec([{'type':'text','id':'a','bbox_norm':[.1,.1,.6,.1],'text':'A'}])
        ppt=self.dir/'m.pptx';Builder(TOKENS,self.dir).build(sp,ppt)
        modified=self.spec([{'type':'text','id':'b','bbox_norm':[.1,.1,.6,.1],'text':'B'}])
        report=compare_structure(modified,ppt,TOKENS)
        self.assertTrue(any(x['issue_type']=='missing_native_element' for x in report['issues']))
    def test_arrow_direction_corruption_detection(self):
        sp=self.spec([{'type':'shape','id':'a','bbox_norm':[.1,.2,.14,.2]},
                      {'type':'shape','id':'b','bbox_norm':[.58,.2,.14,.2]},
                      {'type':'connector','id':'edge','from_id':'a','to_id':'b','arrow':'both'}])
        ppt=self.dir/'a.pptx';Builder(TOKENS,self.dir).build(sp,ppt)
        prs=Presentation(ppt)
        sh=next(s for s in prs.slides[0].shapes if s.name=='edge')
        ln=sh._element.spPr.ln
        for child in list(ln):
            if child.tag.endswith('headEnd'):ln.remove(child)
        prs.save(ppt)
        report=compare_structure(sp,ppt,TOKENS)
        self.assertIn('arrow_mismatch',[x['issue_type'] for x in report['issues']])
    def test_reference_bbox_mismatch(self):
        sp=self.spec([{'type':'shape','id':'target','bbox_norm':[.21,.2,.2,.2],
                       'source_ref':{'bbox_norm':[.15,.2,.2,.2],'verified':True}}])
        ppt=self.dir/'x.pptx';Builder(TOKENS,self.dir).build(sp,ppt)
        issues=compare_structure(sp,ppt,TOKENS)['issues']
        self.assertTrue(any(x['issue_type']=='reference_geometry_mismatch' for x in issues))
    def test_verified_geometry_repair_and_regression(self):
        sp=self.spec([{'type':'shape','id':'target','bbox_norm':[.20,.2,.2,.2],
                       'source_ref':{'bbox_norm':[.16,.2,.2,.2],'verified':True}}])
        ppt=self.dir/'ref.pptx';Builder(TOKENS,self.dir).build(sp,ppt)
        issues=compare_structure(sp,ppt,TOKENS)['issues']
        out=self.dir/'fixed.json'
        report=repair_with_regression(sp,issues,TOKENS,POLICY,out,self.dir/'audit')
        self.assertEqual(report['status'],'ACCEPTED',report)
        self.assertEqual(json.loads(out.read_text())['pages'][0]['elements'][0]['bbox_norm'],[.16,.2,.2,.2])
    def test_bound_translation_repair(self):
        sp=self.spec([{'type':'text','id':'target','bbox_norm':[.81,.3,.2,.2],
                       'text':'保持原文不变','font_size':14}])
        out=self.dir/'bounded.json'
        report=repair_with_regression(sp,detect_spec_bounds(sp),TOKENS,POLICY,out,self.dir/'audit')
        self.assertEqual(report['status'],'ACCEPTED',report)
        e=json.loads(out.read_text())['pages'][0]['elements'][0]
        self.assertEqual(e['text'],'保持原文不变')
        self.assertEqual(e['font_size'],14)
        self.assertLessEqual(e['bbox_norm'][0]+e['bbox_norm'][2],1.000001)
    def test_locked_element_not_modified(self):
        sp=self.spec([{'type':'text','id':'target','bbox_norm':[.81,.3,.2,.2],
                       'text':'不可修改','locked':True}])
        out=self.dir/'untouched.json'
        report=repair_with_regression(sp,detect_spec_bounds(sp),TOKENS,POLICY,out,self.dir/'audit')
        self.assertEqual(report['status'],'ROLLED_BACK')
        self.assertEqual(json.loads(out.read_text()),sp)
    def test_unverified_geometry_not_modified(self):
        sp=self.spec([{'type':'shape','id':'target','bbox_norm':[.2,.3,.2,.2],
                       'source_ref':{'bbox_norm':[.12,.3,.2,.2],'verified':False}}])
        ppt=self.dir/'u.pptx';Builder(TOKENS,self.dir).build(sp,ppt)
        report=repair_with_regression(sp,compare_structure(sp,ppt,TOKENS)['issues'],TOKENS,POLICY,
                                      self.dir/'unsafe.json',self.dir/'audit')
        self.assertEqual(report['status'],'ROLLED_BACK')
    def test_visual_comparison_has_overlay_and_difference(self):
        a=Image.new('RGB',(160,90),'white');b=a.copy()
        ImageDraw.Draw(b).rectangle((30,20,65,70),fill='navy')
        src=self.dir/'ref.png';dst=self.dir/'new.png';a.save(src);b.save(dst)
        r=compare_visual(src,dst,self.dir,'p01')
        self.assertTrue(Path(r['overlay']).exists());self.assertGreater(r['fraction_pixels_above_threshold'],0)
    def test_ratio_mismatch_requests_manual(self):
        a=self.dir/'a.png';b=self.dir/'b.png'
        Image.new('RGB',(160,90)).save(a);Image.new('RGB',(90,160)).save(b)
        r=compare_visual(a,b,self.dir,'p01')
        self.assertEqual(r['status'],'MANUAL_REQUIRED')

if __name__=='__main__':unittest.main()
