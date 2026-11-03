"""Deterministic PPT build from normalized geometry. Native text/shapes/connectors/tables/charts."""
from pathlib import Path
from io import BytesIO
from PIL import Image
import cairosvg
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.oxml.xmlchemy import OxmlElement
from .icon_library import IconLibrary
from .component_registry import expand_spec

SHAPES = {'rect':MSO_SHAPE.RECTANGLE,'roundrect':MSO_SHAPE.ROUNDED_RECTANGLE,
          'ellipse':MSO_SHAPE.OVAL,'chevron':MSO_SHAPE.CHEVRON,
          'triangle':MSO_SHAPE.ISOSCELES_TRIANGLE,'diamond':MSO_SHAPE.DIAMOND}
ALIGN = {'left':PP_ALIGN.LEFT,'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT}


def rgb(hexstr):
    val = str(hexstr).strip().replace('#','')
    if len(val)!=6: raise ValueError(f'Invalid hex color {hexstr}')
    return RGBColor.from_string(val.upper())


def inch_rect(bbox, slide_w, slide_h):
    if len(bbox)!=4 or any(not isinstance(v,(int,float)) for v in bbox):
        raise ValueError('bbox_norm must be four numeric [x,y,w,h] values')
    x,y,w,h=bbox
    if w<=0 or h<=0:raise ValueError('Nonpositive box size')
    return Inches(x*slide_w), Inches(y*slide_h), Inches(w*slide_w), Inches(h*slide_h)


def line_arrow(connector, endpoint='end'):
    ln = connector.get_or_add_ln()
    name='a:tailEnd' if endpoint=='end' else 'a:headEnd'
    el=OxmlElement(name); el.set('type','triangle'); el.set('w','med'); el.set('len','med')
    ln.append(el)


def image_contain(img_path, box):
    with Image.open(img_path) as im: iw,ih=im.size
    x,y,w,h=box
    if iw<=0 or ih<=0:raise ValueError('Invalid image dimension')
    scale=min(w/iw,h/ih)
    actual_w=int(iw*scale); actual_h=int(ih*scale)
    return x+(w-actual_w)//2,y+(h-actual_h)//2,actual_w,actual_h

class Builder:
    def __init__(self, tokens, project_root):
        self.tokens = tokens
        self.project_root = Path(project_root).resolve()
        self.lib = IconLibrary()
        self.ppt = Presentation()
        self.width=float(tokens.get('slide_width_in',13.333333))
        self.height=float(tokens.get('slide_height_in',7.5))
        self.ppt.slide_width=Inches(self.width);self.ppt.slide_height=Inches(self.height)
        self.inventory=[];self.warnings=[]

    def _locate(self, relative):
        path=Path(relative)
        if path.is_absolute():return path
        return (self.project_root/path).resolve()

    def _add_text(self, slide, e, box):
        shape=slide.shapes.add_textbox(*box)
        tf=shape.text_frame; tf.clear();tf.word_wrap=True
        tf.margin_left=Inches(float(e.get('pad_in',.04)))
        tf.margin_right=Inches(float(e.get('pad_in',.04)))
        tf.margin_top=Inches(float(e.get('pad_in',.02)))
        tf.margin_bottom=Inches(float(e.get('pad_in',.02)))
        tf.vertical_anchor={'top':MSO_ANCHOR.TOP,'middle':MSO_ANCHOR.MIDDLE,'bottom':MSO_ANCHOR.BOTTOM}[e.get('v_align','middle')]
        para=tf.paragraphs[0]; para.alignment=ALIGN.get(e.get('align','left'),PP_ALIGN.LEFT)
        para.space_before=Pt(0);para.space_after=Pt(0)
        run=para.add_run();run.text=str(e.get('text',''))
        run.font.name=str(e.get('font',self.tokens.get('body_font','Microsoft YaHei')))
        run.font.size=Pt(float(e.get('font_size',self.tokens.get('body_size_pt',14))))
        run.font.color.rgb=rgb(e.get('color',self.tokens.get('text_color','#243347')))
        run.font.bold=bool(e.get('bold',False))
        if e.get('italic'):run.font.italic=True
        return shape

    def _shape(self, slide, e, box):
        sh=slide.shapes.add_shape(SHAPES[e.get('shape','rect')],*box)
        if e.get('fill','none')=='none':sh.fill.background()
        else:sh.fill.solid();sh.fill.fore_color.rgb=rgb(e['fill'])
        if e.get('line_color'):
            sh.line.color.rgb=rgb(e['line_color']);sh.line.width=Pt(float(e.get('line_width',1)))
        else:sh.line.fill.background()
        return sh

    def _connector(self, slide, e):
        pts=e['points_norm']
        if len(pts)!=4:raise ValueError('points_norm needs [x1,y1,x2,y2]')
        x1,y1,x2,y2=pts
        sh=slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1*self.width),Inches(y1*self.height),Inches(x2*self.width),Inches(y2*self.height))
        sh.line.color.rgb=rgb(e.get('color',self.tokens.get('primary_color','#1E5082')))
        sh.line.width=Pt(float(e.get('line_width',1.8)))
        if e.get('arrow','end') in ('end','both'):line_arrow(sh,'end')
        if e.get('arrow','end') in ('start','both'):line_arrow(sh,'start')
        if e.get('dash'):
            from pptx.enum.dml import MSO_LINE_DASH_STYLE
            sh.line.dash_style=MSO_LINE_DASH_STYLE.DASH
        return sh

    def _icon(self, slide, e, box):
        path,item=self.lib.path(e.get('icon_id') or e.get('term'))
        color=str(e.get('color',self.tokens.get('primary_color','#1E5082'))).replace('#','')
        svg=path.read_text(encoding='utf-8')
        svg=svg.replace('currentColor','#'+color)
        png=cairosvg.svg2png(bytestring=svg.encode('utf-8'),output_width=512,output_height=512)
        shape=slide.shapes.add_picture(BytesIO(png),*box)
        self.warnings.append(f"图标 {item['id']} 插入为高清PNG；仍可移动/缩放，但图标路径不具备原生形状级编辑性")
        return shape

    def _image(self, slide, e, box):
        # 标准图标必须使用 type=icon + icon_id，避免错把裁图当作可复用图标。
        src_parts=Path(e['src']).parts
        if 'icons' in src_parts or e.get('content_role')=='standard_icon':
            raise ValueError('标准图标禁止通过 image/src 传入裁剪图；请使用 type=icon 和 icon_id')
        path=self._locate(e['src'])
        if not path.is_file():raise FileNotFoundError(f'image missing: {path}')
        if e.get('fit','contain')!='contain':
            raise ValueError('基础版本仅支持 contain（不裁切主体），cover 可后续扩展')
        return slide.shapes.add_picture(str(path),*image_contain(path,box))

    def _table(self,slide,e,box):
        data=e['rows']
        if not data or any(len(row)!=len(data[0]) for row in data):raise ValueError('table rows must be nonempty rectangular array')
        rows=len(data);cols=len(data[0]); tbl_shape=slide.shapes.add_table(rows,cols,*box)
        table=tbl_shape.table
        for ri,row in enumerate(data):
            for ci,value in enumerate(row):
                cell=table.cell(ri,ci);cell.text=str(value)
                cell.fill.solid();cell.fill.fore_color.rgb=rgb(e.get('header_fill','#DCEAF4') if ri==0 else e.get('body_fill','#FFFFFF'))
                for p in cell.text_frame.paragraphs:
                    p.alignment=ALIGN.get(e.get('align','center'))
                    for r in p.runs:
                        r.font.name=self.tokens.get('body_font','Microsoft YaHei')
                        r.font.size=Pt(float(e.get('font_size',12)))
                        r.font.color.rgb=rgb(e.get('text_color','#243347'))
                        r.font.bold=(ri==0)
        return tbl_shape

    def _chart(self,slide,e,box):
        cats=e.get('categories',[]);series=e.get('series',[])
        if not cats or not series:raise ValueError('chart must provide data; do not invent values')
        cd=CategoryChartData();cd.categories=cats
        for s in series:
            if len(s['values'])!=len(cats):raise ValueError('chart series/categories mismatch')
            cd.add_series(s['name'],s['values'])
        shp=slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,*box,cd)
        shp.chart.has_legend=len(series)>1
        return shp

    def _element(self,slide,e,page_id):
        family=e['type'];eid=e.get('id',f'{page_id}_element_{len(self.inventory)+1}')
        if family=='connector':
            obj=self._connector(slide,e); editable=True
            bbox=e['points_norm']
        else:
            bbox=e['bbox_norm'];box=inch_rect(bbox,self.width,self.height)
            if family=='text':obj=self._add_text(slide,e,box)
            elif family=='shape':obj=self._shape(slide,e,box)
            elif family=='icon':obj=self._icon(slide,e,box)
            elif family=='image':obj=self._image(slide,e,box)
            elif family=='table':obj=self._table(slide,e,box)
            elif family=='chart':obj=self._chart(slide,e,box)
            else:raise ValueError(f'Unsupported element type: {family}')
            editable=family in ('text','shape','table','chart')
        obj.name=eid
        # Real-case regression: PowerPoint theme may add unwanted drop shadows.
        # Standard generated elements should have no implicit theme effects.
        for effect in obj._element.xpath('.//a:effectRef'):
            effect.set('idx','0')
        self.inventory.append({'page_id':page_id,'element_id':eid,'family':family,'bbox_norm':bbox,
                               'native_editable':editable,'confidence':e.get('confidence',None)})
        return obj

    def build(self, spec, out):
        # Optional per-deck canvas size, used by OCR-assisted reconstruction drafts.
        # Existing v4.2 specs remain unchanged and continue to use design_tokens.json.
        slide_size = spec.get('slide_size_in')
        if slide_size is not None:
            if not isinstance(slide_size, (list, tuple)) or len(slide_size) != 2:
                raise ValueError('slide_size_in must be [width_in, height_in]')
            width, height = float(slide_size[0]), float(slide_size[1])
            if not (1.0 <= width <= 40.0 and 1.0 <= height <= 40.0):
                raise ValueError('slide_size_in values must be between 1 and 40 inches')
            self.width, self.height = width, height
            self.ppt.slide_width = Inches(width)
            self.ppt.slide_height = Inches(height)
        spec=expand_spec(spec,self.tokens)
        pages=spec.get('pages',[])
        if not pages:raise ValueError('No pages in spec')
        for i,page in enumerate(pages):
            pid=page.get('page_id',f'slide_{i+1:03d}')
            slide=self.ppt.slides.add_slide(self.ppt.slide_layouts[6])
            bg=slide.background.fill;bg.solid();bg.fore_color.rgb=rgb(page.get('background',self.tokens.get('background','#FFFFFF')))
            for e in page.get('elements',[]):self._element(slide,e,pid)
        out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
        self.ppt.save(str(out))
        return out
