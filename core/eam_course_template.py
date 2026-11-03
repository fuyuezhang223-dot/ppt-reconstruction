"""Reusable editable EAM/industrial course slide layout component.

Architecture: content-only JSON + one shared master renderer + 3 body layout families.
All textual content, cards, borders, arrows, bullets, status markers and waves
are PowerPoint objects. Industry skyline and photographs are image layers.
The caller retains original references for fidelity QA.
"""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
from functools import lru_cache
import json, math
from PIL import Image,ImageDraw
import cairosvg
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN,MSO_ANCHOR
from pptx.dml.color import RGBColor
from .icon_library import IconLibrary

PAGE_W, PAGE_H = 1672, 941
SX, SY = 13.333333/PAGE_W,7.5/PAGE_H
FONT = 'Noto Sans CJK SC'
COLORS={'navy':'#07356F','dark':'#062B60','blue':'#078EF3','royal':'#0D83ED','pale':'#E7F5FE',
'line':'#9CD7FF','cyan':'#33B8D1','orange':'#FFAE24','purple':'#795BFC','teal':'#00BAAD'}


def p_x(x):return Inches(float(x)*SX)
def p_y(y):return Inches(float(y)*SY)
def cl(s):return RGBColor.from_string(str(s).lstrip('#').upper())

class EAMRenderer:
    def __init__(self,project_root:Path):
        self.root=Path(project_root).resolve()
        self.icon_lib=IconLibrary()
        self.ppt=Presentation();self.ppt.slide_width=Inches(13.333333);self.ppt.slide_height=Inches(7.5)
        self.registry=[];self.missing_icons=[];self.slide_index=0;self.page_num=0

    def log(self, obj, id, kind, source=None):
        obj.name=f'{self.slide_index:02d}_{id}'
        # Suppress PowerPoint theme shadow/effect on native shapes.
        # This was a real-world fidelity regression found on six references.
        for effect in obj._element.xpath('.//a:effectRef'):
            effect.set('idx','0')
        self.registry.append({'slide_index':self.slide_index,'id':id,'ppt_object_name':obj.name,'kind':kind,
                              'native_editable': kind in ('text','shape','connector'),
                              'source':source or ''})
        return obj

    def text(self,sl,id,txt,x,y,w,h,size=20,color=COLORS['dark'],bold=False,align='left',vertical='middle',
             font=FONT,margin=0):
        sh=sl.shapes.add_textbox(p_x(x),p_y(y),p_x(w),p_y(h))
        tf=sh.text_frame;tf.clear();tf.word_wrap=False
        tf.margin_left=Inches(margin);tf.margin_right=Inches(margin);tf.margin_top=0;tf.margin_bottom=0
        tf.vertical_anchor={'middle':MSO_ANCHOR.MIDDLE,'top':MSO_ANCHOR.TOP,'bottom':MSO_ANCHOR.BOTTOM}[vertical]
        para=tf.paragraphs[0];para.alignment={'left':PP_ALIGN.LEFT,'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT}[align]
        para.space_before=Pt(0);para.space_after=Pt(0)
        run=para.add_run();run.text=txt;run.font.name=font;run.font.size=Pt(size);run.font.bold=bool(bold)
        run.font.color.rgb=cl(color)
        # East Asian font binding: improves portability vs only western typeface.
        rpr=run._r.get_or_add_rPr()
        from pptx.oxml.xmlchemy import OxmlElement
        ea=OxmlElement('a:ea');ea.set('typeface',font);rpr.append(ea)
        return self.log(sh,id,'text')

    def rect(self,sl,id,x,y,w,h,fill='none',stroke=None,sw=1,rounded=False):
        shape=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                p_x(x),p_y(y),p_x(w),p_y(h))
        if rounded:
            try:shape.adjustments[0]=.13
            except Exception:pass
        if fill=='none':shape.fill.background()
        else:shape.fill.solid();shape.fill.fore_color.rgb=cl(fill)
        if stroke:shape.line.color.rgb=cl(stroke);shape.line.width=Pt(sw)
        else:shape.line.fill.background()
        return self.log(shape,id,'shape')

    def oval(self,sl,id,x,y,w,h,fill,stroke=None,sw=1):
        shape=sl.shapes.add_shape(MSO_SHAPE.OVAL,p_x(x),p_y(y),p_x(w),p_y(h))
        shape.fill.solid();shape.fill.fore_color.rgb=cl(fill)
        if stroke:shape.line.color.rgb=cl(stroke);shape.line.width=Pt(sw)
        else:shape.line.fill.background()
        return self.log(shape,id,'shape')

    def poly(self,sl,id,points,fill,stroke=None,sw=1):
        builder=sl.shapes.build_freeform(start_x=p_x(points[0][0]),start_y=p_y(points[0][1]),scale=1)
        builder.add_line_segments([(p_x(x),p_y(y)) for x,y in points[1:]],close=True)
        sh=builder.convert_to_shape()
        sh.fill.solid();sh.fill.fore_color.rgb=cl(fill)
        if stroke:sh.line.color.rgb=cl(stroke);sh.line.width=Pt(sw)
        else:sh.line.fill.background()
        return self.log(sh,id,'shape')

    def line(self,sl,id,x1,y1,x2,y2,color='#9FC8E7',sw=1):
        sh=sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,p_x(x1),p_y(y1),p_x(x2),p_y(y2))
        sh.line.color.rgb=cl(color);sh.line.width=Pt(sw)
        return self.log(sh,id,'connector')

    def photo(self,sl,id,path,x,y,w,h):
        if 'icons' in Path(path).parts or Path(path).name.startswith(('header_gear','header_clipboard','course_emblem')):
            raise ValueError(f'标准图标不得使用截图裁剪资源: {path}; 请改用 self.icon() 图标库')
        sh=sl.shapes.add_picture(str((self.root/path).resolve()),p_x(x),p_y(y),p_x(w),p_y(h))
        return self.log(sh,id,'image',path)

    @lru_cache(maxsize=128)
    def icon_png(self,keyword,color):
        path,item=self.icon_lib.path(keyword)
        svg=path.read_text(encoding='utf8')
        svg=svg.replace('currentColor',color)
        return cairosvg.svg2png(bytestring=svg.encode('utf8'),output_width=256,output_height=256),item['id']

    def icon(self,sl,id,term,color,x,y,w,h):
        try: png,icon_id=self.icon_png(term,color)
        except Exception as exc:
            self.missing_icons.append(term)
            raise ValueError(f'标准图标在SVG库中未找到: {term}') from exc
        sh=sl.shapes.add_picture(BytesIO(png),p_x(x),p_y(y),p_x(w),p_y(h))
        return self.log(sh,id,'icon_png',icon_id)

    def base(self,sl,conf):
        pid=str(conf['page_num'])
        self.rect(sl,'background',0,0,PAGE_W,PAGE_H,fill='#FFFFFF')
        # Native polygons approximate recurring corner motifs from sources.
        self.poly(sl,'bottom_left_light',[(0,787),(28,833),(90,870),(205,890),(308,904),(384,941),(0,941)],'#D1ECF9')
        self.poly(sl,'bottom_left_medium',[(0,826),(45,872),(107,901),(207,905),(286,928),(320,941),(0,941)],'#42A8D2')
        self.poly(sl,'bottom_left_blue',[(0,857),(32,894),(115,915),(187,920),(244,941),(0,941)],'#0E78AC')
        self.poly(sl,'bottom_right_blue',[(1672,797),(1652,823),(1617,836),(1590,850),(1561,892),
                                         (1533,911),(1507,927),(1489,941),(1672,941)],'#013970')
        # Industrial skyline is a reusable, independent image asset; overlay it before title.
        self.photo(sl,'master/industrial_skyline','assets/industrial_skyline.png',868,74,804,207)
        self.oval(sl,'master/course_emblem_bg',54,18,64,64,COLORS['navy'])
        self.icon(sl,'master/course_emblem_icon','ORG-026','#FFFFFF',68,31,36,36)
        self.text(sl,'master/course_title','智能制造与管理系列课程  |  EAM资产管理',138,25,660,46,14.2,color=COLORS['navy'])
        self.rect(sl,'master/chapter_badge',1296,20,135,53,COLORS['navy'],rounded=True)
        self.text(sl,'master/chapter_text','第9章',1300,23,130,47,17.5,'#FFFFFF',True,'center')
        self.text(sl,'master/topic','点检管理',1447,25,159,43,16.5,COLORS['navy'],True)
        self.text(sl,'master/big_title',conf['title'],58,105,1100,111,
                  54 if len(conf['title'])<=9 else 39 if len(conf['title'])<=13 else 36,
                  COLORS['navy'],True)
        self.text(sl,'master/subtitle',conf['subtitle'],60,213,1190,67,26.5,COLORS['blue'],False)

    def summary(self,sl,conf):
        top=conf.get('summary_y',809);h=80
        self.rect(sl,'summary/container',55,top,1549,h,fill='#FFFDFC',stroke='#FFA536',sw=.75,rounded=True)
        self.oval(sl,'summary/orange_emblem_bg',102,top+7,79,69,'#FF8A24')
        # 标准徽章来自本地图标库，不从参考图裁剪。
        self.icon(sl,'summary/icon','QUA-005','#FFFFFF',121,top+23,41,35)
        self.line(sl,'summary/orange_rule',216,top+19,216,top+60,color='#FF6B13',sw=1.45)
        self.text(sl,'summary/label','核心价值：',240,top+11,196,59,22.1,'#F45E13',True)
        self.text(sl,'summary/value',conf['summary'],420,top+11,1110,59,19.3,COLORS['dark'],True)

    def header_band(self,sl,prefix,title,x,y,w):
        self.rect(sl,prefix+'/band',x,y,w,67,fill='#E4F4FC',rounded=True)
        icon_term='settings-cog' if title in ('编制步骤','计划逻辑','流程步骤','保养维度') else 'clipboard-check'
        self.icon(sl,prefix+'/icon',icon_term,COLORS['royal'],x+21,y+13,52,46)
        self.text(sl,prefix+'/title',title,x+111,y+7,w-125,53,22,COLORS['dark'],True)

    def step_card(self,sl,base,num,title,x,y,w,h,icon_term,center_y=None,icon_color=None):
        self.rect(sl,base+'/card',x,y,w,h,fill='#FFFFFF',stroke=COLORS['line'],sw=.85,rounded=True)
        num_colors=['#31B0F9','#31BACE','#FFAE2C','#8067FF','#02BBAE']
        self.rect(sl,base+'/number_bg',x+12,y+7,65,52,fill=num_colors[num-1],rounded=True)
        self.text(sl,base+'/number',f'{num:02d}',x+12,y+8,65,47,22,'#FFFFFF',False,'center')
        if center_y is None:center_y=y+76
        cx=x+(w-110)/2
        self.oval(sl,base+'/icon_halo',cx,center_y,110,110,'#EAF6FD')
        self.icon(sl,base+'/icon',icon_term,icon_color or COLORS['royal'],cx+25,center_y+24,60,61)
        title_size=17.9 if len(title)<=6 else 16.3
        self.text(sl,base+'/title',title,x+8,y+h-61,w-16,48,title_size,COLORS['dark'],True,'center')

    def arrow(self,sl,id,x,y):
        self.poly(sl,id,[(x,y-16),(x+20,y),(x,y+16)],'#42B5F8')

    def four_step_page(self,sl,conf):
        # Main panel shape / size consistent across slides.
        x=54;y=292;w=1024
        if conf['layout']=='four_205':
            y=292; top_h=289;photo_box=(1068,294,536,504); lower_y=594;lower_h=201;card_y=374
            w=998
        else:
            top_h=289;photo_box=(1097,293,506,504);lower_y=595;lower_h=199;card_y=375
        self.rect(sl,'body/step_panel',x,y,w,top_h,fill='#FFFFFF',stroke=COLORS['line'],sw=.8,rounded=True)
        self.header_band(sl,'body/main_heading',conf['section'],x+5,y+8,w-12)
        n=len(conf['steps']);gap=36;left=x+23;avail=w-46;cw=(avail-gap*(n-1))/n
        icons=conf['step_icons']
        for i,item in enumerate(conf['steps']):
            bx=left+i*(cw+gap)
            self.step_card(sl,f'body/step_{i+1}',i+1,item,bx,card_y,cw,192,icons[i],center_y=card_y+28)
            if i<n-1:self.arrow(sl,f'body/arrow_{i+1}',bx+cw+7,card_y+96)
        self.rect(sl,'body/lower_panel',x,lower_y,w,lower_h,fill='#FFFFFF',stroke=COLORS['line'],sw=.8,rounded=True)
        self.header_band(sl,'body/lower_heading',conf['lower_heading'],x+4,lower_y+5,w-8)
        lower_items=conf['bullets']
        leftcol=x+25;rightcol=x+w/2+14
        self.line(sl,'body/midline',x+w/2,lower_y+90,x+w/2,lower_y+183, '#A8D7F4',1.2)
        for i,txt in enumerate(lower_items):
            col=i%2;row=i//2
            bx=leftcol if col==0 else rightcol;by=lower_y+93+row*54
            self.oval(sl,f'body/bullet_{i+1}',bx,by+12,18,18,COLORS['royal'])
            self.text(sl,f'body/bullet_text_{i+1}',txt,bx+35,by,442,47,16.7,COLORS['dark'])
        self.photo(sl,'body/worker_photo',f'assets/worker_{conf["page_num"]}.png',*photo_box)

    def five_step_page(self,sl,conf):
        xs=[57,267,469,674,879]; widths=[194,191,190,191,190];y=310
        for i,(x,w,txt,ic) in enumerate(zip(xs,widths,conf['steps'],conf['step_icons'])):
            self.step_card(sl,f'body/step_{i+1}',i+1,txt,x,y,w,294,ic,center_y=y+89,icon_color=['#238BFF','#238BFF','#238BFF','#7A63FF','#18C2AF'][i])
            if i<4:self.arrow(sl,f'body/arrow_{i+1}',x+w+4,y+157)
        self.photo(sl,'body/worker_photo',f'assets/worker_{conf["page_num"]}.png',1092,300,515,458)
        self.rect(sl,'body/lower_focus_panel',57,628,1012,122,fill='#EEF9FF',stroke=COLORS['line'],sw=.85,rounded=True)
        self.rect(sl,'body/lower_focus_iconbg',77,647,80,79,fill='#2EA7FC',rounded=True)
        self.icon(sl,'body/lower_focus_icon','MFG-010','#FFFFFF',94,665,48,45)
        self.text(sl,'body/lower_focus_heading','管理关注',178,655,174,58,22,COLORS['navy'],True)
        bx=371
        for i,t in enumerate(conf['bullets']):
            if i: self.line(sl,f'body/focus_split_{i}',bx+(i-1)*179,669,bx+(i-1)*179,714,'#ABD9F6',1)
            self.oval(sl,f'body/focus_dot_{i+1}',bx+i*179+10,678,15,15,COLORS['royal'])
            self.text(sl,f'body/focus_text_{i+1}',t,bx+i*179+35,659,150,56,16.1,COLORS['dark'])

    def comparison_page(self,sl,conf):
        # Two panels; intentionally not expressed as normal step flow.
        left=(60,290,520,418);right=(663,290,489,418)
        for n,(x,y,w,h),title,bg,head_icon in [('prevention',left,'预防性维护','#E7F5FC','MFG-010'),
                                               ('correction',right,'纠正性维护','#FFF2E5','MFG-013')]:
            self.rect(sl,f'body/{n}/container',x,y,w,h,'#FFFFFF',stroke=COLORS['line'],sw=.85,rounded=True)
            self.rect(sl,f'body/{n}/heading_bg',x+4,y+7,w-8,82,bg,rounded=True)
            c='#238BFF' if n=='prevention' else '#F4770D'
            self.oval(sl,f'body/{n}/head_icon_bg',x+23,y+7,82,78,c)
            self.icon(sl,f'body/{n}/head_icon',head_icon,'#FFFFFF',x+39,y+26,50,42)
            self.text(sl,f'body/{n}/heading',title,x+142,y+12,w-157,68,25.6,COLORS['navy'],True)
            row_icons=conf['pre_icons'] if n=='prevention' else conf['post_icons']
            rows=conf['pre_rows'] if n=='prevention' else conf['post_rows']
            for j,(txt,term) in enumerate(zip(rows,row_icons)):
                yy=y+99+107*j
                if j: self.line(sl,f'body/{n}/split_{j}',x+42,yy-6,x+w-34,yy-6,'#BCDDF4',.8)
                self.oval(sl,f'body/{n}/row_{j+1}_halo',x+42,yy,92,90,'#EAF6FC' if n=='prevention' else '#FFF1E4')
                self.icon(sl,f'body/{n}/row_{j+1}_icon',term,c,x+60,yy+17,58,55)
                self.text(sl,f'body/{n}/row_{j+1}_text',txt,x+177,yy+10,w-191,67,21.3,COLORS['navy'],True)
        self.line(sl,'body/vs_rule',622,376,622,669,'#B5D6EC',1.1)
        self.oval(sl,'body/vs_bg',581,465,82,82,'#43B2F8')
        self.text(sl,'body/vs_text','VS',586,470,73,72,23.3,'#FFFFFF',True,'center')
        self.photo(sl,'body/worker_photo',f'assets/worker_{conf["page_num"]}.png',1171,292,433,421)
        self.rect(sl,'body/advice',56,727,1548,80,'#E9F8FF',stroke=COLORS['line'],sw=.9,rounded=True)
        self.oval(sl,'body/advice_icon_bg',78,729,81,75,'#249BFC')
        self.icon(sl,'body/advice_icon','MGT-005','#FFFFFF',97,745,45,41)
        self.text(sl,'body/advice_label','应用建议',184,738,171,59,21.5,COLORS['navy'],True)
        self.line(sl,'body/advice_rule',376,748,376,786,'#80C6F1',1.1)
        self.text(sl,'body/advice_body',conf['advice'],415,739,1120,58,20.5,COLORS['dark'])

    def render_page(self,conf):
        self.slide_index+=1;self.page_num=int(conf['page_num']);sl=self.ppt.slides.add_slide(self.ppt.slide_layouts[6])
        self.base(sl,conf)
        match conf['layout']:
            case 'four'|'four_205':self.four_step_page(sl,conf)
            case 'five':self.five_step_page(sl,conf)
            case 'comparison':self.comparison_page(sl,conf)
            case _:raise ValueError('Unknown EAM layout: '+str(conf['layout']))
        self.summary(sl,conf)
        # The navy corner and page number must overlay the footer summary's
        # right edge; otherwise the page number is clipped on slide 208.
        self.poly(sl,'master/bottom_right_foreground',[(1672,797),(1652,823),(1617,836),(1590,850),
                 (1561,892),(1533,911),(1507,927),(1489,941),(1672,941)],'#013970')
        self.text(sl,'master/page_number',str(conf['page_num']),1570,874,81,57,20.8,'#FFFFFF',False,'center')
        return sl

    def build(self,spec,output):
        for page in spec['pages']:self.render_page(page)
        output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
        self.ppt.save(output)
        output.with_suffix('.inventory.json').write_text(json.dumps(self.registry,ensure_ascii=False,indent=2),encoding='utf-8')
        return output
