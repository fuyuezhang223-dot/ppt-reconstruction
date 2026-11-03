"""Machine-checkable QA. Text overflow/semantic correctness remain visual/manual checks."""
from pptx import Presentation
from pathlib import Path
import json


def inspect_pptx(path, expected_pages=None, minimum_body_pt=12):
    prs=Presentation(str(path))
    issues=[];counts={'native_text':0,'native_shape_or_connector':0,'native_table':0,'native_chart':0,'raster_or_svg_pictures':0}
    w,h=prs.slide_width,prs.slide_height
    if expected_pages is not None and len(prs.slides)!=expected_pages:
        issues.append({'level':'P0','page':None,'detail':f'页数错误：{len(prs.slides)} != {expected_pages}'})
    for n,slide in enumerate(prs.slides,1):
        text_rects=[]
        for sh in slide.shapes:
            if sh.left < -10000 or sh.top < -10000 or sh.left+sh.width > w+10000 or sh.top+sh.height>h+10000:
                issues.append({'level':'P0','page':n,'detail':f'元素 {sh.shape_id} 超出画布'})
            if sh.has_text_frame and sh.text.strip():
                counts['native_text']+=1
                text_rects.append((sh.shape_id,sh.left,sh.top,sh.left+sh.width,sh.top+sh.height))
                for para in sh.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.size and run.font.size.pt+0.001 < minimum_body_pt:
                            issues.append({'level':'P0','page':n,'detail':f'文本 {sh.shape_id} 小于{minimum_body_pt}pt：{run.font.size.pt:.1f}pt'})
            elif sh.has_table:counts['native_table']+=1
            elif sh.has_chart:counts['native_chart']+=1
            elif sh.shape_type==13:counts['raster_or_svg_pictures']+=1
            else:counts['native_shape_or_connector']+=1
        for i,a in enumerate(text_rects):
            for b in text_rects[i+1:]:
                x_overlap=min(a[3],b[3])-max(a[1],b[1]);y_overlap=min(a[4],b[4])-max(a[2],b[2])
                if x_overlap>0 and y_overlap>0:
                    area=x_overlap*y_overlap
                    area_a=max(1,(a[3]-a[1])*(a[4]-a[2]));area_b=max(1,(b[3]-b[1])*(b[4]-b[2]))
                    if area/min(area_a,area_b)>.12:
                        issues.append({'level':'P1','page':n,'detail':f'文本框 {a[0]} 和 {b[0]} 几何重叠，需目视复核'})
    return {'file':str(path),'slides':len(prs.slides),'counts':counts,'issues':issues,
            'P0':sum(x['level']=='P0' for x in issues),'P1':sum(x['level']=='P1' for x in issues),
            'machine_check_scope':['PPTX可打开','页数','对象出界','显式字号下限','文本框重叠'],
            'manual_visual_checks_required':['中文字体替换与换行','文字实际溢出','图标语义与视觉重量','箭头所指业务逻辑','参考图相似度','图片主体是否被误裁','文本内容与数值正确性']}


def save_report(report,path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')


def render_preview(pptx_path,outdir):
    import shutil,subprocess,tempfile
    from PIL import Image,ImageOps,ImageDraw
    import fitz
    office=shutil.which('libreoffice') or shutil.which('soffice') or shutil.which('soffice.exe') or shutil.which('libreoffice.exe')
    if not office:return {'status':'NOT_AVAILABLE','detail':'没有安装LibreOffice/soffice，无法自动渲染。请使用PowerPoint/WPS导出图片后进行视觉QA。'}
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    pdf=outdir/(Path(pptx_path).stem+'.pdf')
    with tempfile.TemporaryDirectory(prefix='pptx_lo_profile_') as profile:
        cmd=[office,'-env:UserInstallation='+Path(profile).resolve().as_uri(),'--headless','--convert-to','pdf','--outdir',str(outdir),str(pptx_path)]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    if result.returncode!=0 or not pdf.exists():return {'status':'FAILED','detail':(result.stderr or result.stdout)[-600:]}
    previews=[];doc=fitz.open(pdf)
    thumbs=[]
    for i,page in enumerate(doc,1):
        pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
        f=outdir/f'slide_{i:03d}.png';pix.save(f);previews.append(str(f))
        with Image.open(f) as im:
            small=im.convert('RGB');small.thumbnail((440,260))
            tile=Image.new('RGB',(480,300),'#E6E9EF');tile.paste(small,((480-small.width)//2,22))
            ImageDraw.Draw(tile).text((12,279),f'Slide {i:03d}',fill='#222222')
            thumbs.append(tile)
    cols=3;rows=(len(thumbs)+cols-1)//cols
    wall=Image.new('RGB',(480*cols,300*rows),'white')
    for i,im in enumerate(thumbs):wall.paste(im,((i%cols)*480,(i//cols)*300))
    contact=outdir/'contact_sheet.png';wall.save(contact)
    return {'status':'PASS','slide_previews':previews,'contact_sheet':str(contact),'pdf':str(pdf)}
