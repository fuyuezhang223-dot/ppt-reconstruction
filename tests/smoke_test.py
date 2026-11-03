"""Regression smoke test, run from repository root: python -m tests.smoke_test."""
import json, tempfile
from pathlib import Path
from pptx import Presentation
from core.ppt_builder import Builder
from core.quality import inspect_pptx
from core.icon_library import IconLibrary
ROOT=Path(__file__).resolve().parents[1]
TOKENS=json.loads((ROOT/'config/design_tokens.json').read_text(encoding='utf8'))
SPEC=json.loads((ROOT/'examples/demo_deck.json').read_text(encoding='utf8'))
assert len(IconLibrary().items)==500
assert IconLibrary().path('MFG-001')[0].exists()
with tempfile.TemporaryDirectory() as work:
    dst=Path(work)/'smoke.pptx'
    Builder(TOKENS, ROOT/'examples').build(SPEC,dst)
    prs=Presentation(dst)
    assert len(prs.slides)==1
    slide=prs.slides[0]
    assert sum(sh.has_text_frame and bool(sh.text) for sh in slide.shapes)>=8
    assert sum(sh.shape_type==9 for sh in slide.shapes)==2
    report=inspect_pptx(dst,expected_pages=1)
    assert report['P0']==0,report
    assert report['P1']==0,report
    spec2={'pages':[{'page_id':'test_table_chart','elements':[
        {'type':'table','id':'tbl','bbox_norm':[.04,.1,.4,.35], 'rows':[['指标','值'],['A','3']], 'font_size':12},
        {'type':'chart','id':'cht','bbox_norm':[.5,.1,.45,.6], 'categories':['A','B'],'series':[{'name':'值','values':[3,4]}]}
    ]}]}
    dst2=Path(work)/'data.pptx';Builder(TOKENS,ROOT).build(spec2,dst2)
    slide2=Presentation(dst2).slides[0]
    assert any(s.has_chart for s in slide2.shapes)
    assert any(s.has_table for s in slide2.shapes)
print('Smoke test PASS: 500 icons indexed, native text+shapes+connectors+table+chart, pptx QA')
