"""Usage from any directory:
python examples/real_cases/eam_6pages/build.py
Reuses v4.2 core/EAMCourseTemplate, accepts content in pages.json.
"""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[2]))
from core.eam_course_template import EAMRenderer
from core.quality import inspect_pptx,render_preview
from core.reference_compare import compare_visual
out=ROOT/'outputs';out.mkdir(exist_ok=True)
spec=json.loads((ROOT/'pages.json').read_text(encoding='utf8'))
renderer=EAMRenderer(ROOT)
pptx=renderer.build(spec,out/'EAM_6pages_editable.pptx')
report=inspect_pptx(pptx,expected_pages=6,minimum_body_pt=12)
report['source_count']=6
report['icon_missing']=renderer.missing_icons
report['editability_notes']='人物照片、工业背景与SVG库图标渲染成的高清 PNG 属于独立图片；文字、卡片、箭头为原生 PowerPoint 对象。标准图标没有从截图裁剪。'
report['preview']=render_preview(pptx,out/'preview')
if report['preview']['status']!='PASS':
    print('提示：本机无法自动导出最新预览；请用 PowerPoint/WPS 导出后再运行视觉/文字审计，勿沿用旧预览。')
visual=[]
for i,page in enumerate(spec['pages'],start=1):
    ref=(ROOT/page['reference_image'])
    rend=out/'preview'/f'slide_{i:03d}.png'
    if report['preview']['status']=='PASS' and rend.exists():visual.append(compare_visual(ref,rend,out/'comparisons',f'slide_{page["page_num"]}',pixel_threshold=52))
report['visual_comparison']=visual
from core.icon_library import IconLibrary
icon_lib=IconLibrary()
icon_usage=[]
for item in renderer.registry:
    if item['kind']=='icon_png':
        path,meta=icon_lib.path(item['source'])
        icon_usage.append({'slide_index':item['slide_index'],'element_id':item['id'],'icon_id':meta['id'],
                           'svg_path':str(path.relative_to(icon_lib.root))})
(out/'ICON_SOURCE_MANIFEST.json').write_text(json.dumps({'policy':'标准图标仅由本地 SVG 库加载；不允许截图裁图；本版库图标经 CairoSVG 渲染为高清 PNG 对象','count':len(icon_usage),'objects':icon_usage},ensure_ascii=False,indent=2),encoding='utf8')
if renderer.missing_icons:
    raise RuntimeError(f'有未找到的标准图标，禁止交付: {renderer.missing_icons}')
(out/'QA_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('Wrote',pptx,'QA P0/P1:',report['P0'],report['P1'],'pictures',report['counts']['raster_or_svg_pictures'])
