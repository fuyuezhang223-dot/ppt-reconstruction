"""Real screenshot integration QA: PDF text-line integrity, editable object structure,
paired visual references. Does not claim full pixel-perfect matching.
"""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
from pptx import Presentation
import fitz
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'outputs'
spec=json.loads((ROOT/'pages.json').read_text(encoding='utf8'))
qa=json.loads((OUT/'QA_REPORT.json').read_text(encoding='utf8'))
ppt=Presentation(OUT/'EAM_6pages_editable.pptx')
pdf=fitz.open(OUT/'preview/EAM_6pages_editable.pdf')
assert len(ppt.slides)==len(pdf)==6
results=[]
for idx,page in enumerate(spec['pages']):
    texts=[]
    for sh in ppt.slides[idx].shapes:
        if sh.has_text_frame and sh.text.strip():texts.append(sh.text.strip())
    pdf_lines=[ ''.join(span['text'] for span in line['spans'])
                for block in pdf[idx].get_text('dict')['blocks']
                for line in block.get('lines',[]) ]
    mandatory=[page['title'],page['subtitle'],page['summary']]
    if 'steps' in page: mandatory += page['steps']
    if 'bullets' in page: mandatory+=page['bullets']
    if page.get('layout')=='comparison': mandatory+=page['pre_rows']+page['post_rows']+[page['advice']]
    missing=[txt for txt in mandatory if txt not in texts]
    singleline=page['title'] in pdf_lines
    img_count=sum(1 for sh in ppt.slides[idx].shapes if sh.shape_type==13)
    fullslide_images=[sh.name for sh in ppt.slides[idx].shapes
                      if sh.shape_type==13 and sh.width>ppt.slide_width*.80 and sh.height>ppt.slide_height*.80]
    results.append({'page_num':page['page_num'],'layout':page['layout'],'text_integrity_missing':missing,
                    'title_rendered_single_line':singleline,'independent_images':img_count,
                    'full_slide_images':fullslide_images,'p0': bool(missing or not singleline or fullslide_images)})
visual={x['page_id']:x for x in qa['visual_comparison']}
report={'title':'EAM six-page real-world editable PPT reconstruction audit',
        'slides':len(ppt.slides),'programmatic_qa':{'P0':qa['P0'],'P1':qa['P1']},
        'native_editability_object_count':qa['counts']['native_text']+qa['counts']['native_shape_or_connector'],
        'independent_image_object_count':qa['counts']['raster_or_svg_pictures'],
        'native_object_share':round((qa['counts']['native_text']+qa['counts']['native_shape_or_connector'])/sum(qa['counts'].values()),4),
        'per_page':results,
        'reference_visual_diagnostic':[{ 'page':x['page_num'],
           'mean_abs_channel_difference':visual['slide_'+str(x['page_num'])]['mean_abs_pixel_difference'],
           'pixel_fraction_above_threshold':visual['slide_'+str(x['page_num'])]['fraction_pixels_above_threshold']}
           for x in results],
        'icon_policy':{'source_crop_icon_objects':0,'library_icon_objects':sum(1 for x in json.loads((OUT/'EAM_6pages_editable.inventory.json').read_text(encoding='utf8')) if x['kind']=='icon_png'),'policy':'标准图标仅调用 SVG 库并在当前引擎中渲染为可独立移动的高清 PNG'},
        'manual_review_limitations':[
           '视觉差异数值不等于版式准确率；字体抗锯齿、图标处理、背景插画均影响像素结果',
           '原生文字、卡片、流程线可编辑；设备照片、工业线稿和具体图标为独立图片',
           '标准图标来自 SVG 图标库，当前插入为独立高清 PNG；矢量路径不可逐点编辑',
           '缩略图审核不能证明每个视觉元素像素级一致',
           '未经原始 PPTX 文件，截图中可能被遮挡或未知的内容无法保证还原']}
(OUT/'REAL_CASE_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
# Visual paired contact (reference on left, regenerated editable slide on right)
font_candidates=[
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    'C:/Windows/Fonts/msyh.ttc',
    'C:/Windows/Fonts/simhei.ttf',
]
font=next((ImageFont.truetype(f,25) for f in font_candidates if Path(f).exists()),ImageFont.load_default())
W=750;H=422
wall=Image.new('RGB',(2*W,6*(H+47)),'#E9EFF5');draw=ImageDraw.Draw(wall)
for i,item in enumerate(results):
    number=item['page_num']
    src=Image.open(ROOT/'references'/f'slide_{number}.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
    dst=Image.open(OUT/'preview'/f'slide_{i+1:03d}.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
    yy=i*(H+47);wall.paste(src,(0,yy+47));wall.paste(dst,(W,yy+47))
    draw.text((18,yy+6),f'{number} · 参考图片',font=font,fill='#163A62')
    draw.text((W+18,yy+6),f'{number} · 可编辑 PPT 渲染',font=font,fill='#163A62')
wall.save(OUT/'REFERENCE_VS_EDITABLE.png')
registry=json.loads((OUT/'EAM_6pages_editable.inventory.json').read_text(encoding='utf8'))
assert not any('assets/icons/' in (entry.get('source') or '') for entry in registry)
assert not any(entry['id'].endswith('source_icon') for entry in registry)
assert report['icon_policy']['library_icon_objects']>0
print('Audit:',json.dumps({'slides':report['slides'],'native_share':report['native_object_share'],
                           'missing_text':sum(len(r['text_integrity_missing']) for r in results),
                           'title_wraps':sum(not r['title_rendered_single_line'] for r in results),
                           'fullslide_images':sum(len(r['full_slide_images']) for r in results)},ensure_ascii=False))
assert not any(r['p0'] for r in results)
