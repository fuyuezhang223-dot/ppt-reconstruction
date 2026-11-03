"""Structural/geometry tests + optional reference/render visual differences.
A pixel similarity score is a diagnostic, NEVER a hard claim of fidelity.
"""
from pathlib import Path
import json
from copy import deepcopy
from PIL import Image,ImageChops,ImageEnhance,ImageDraw
import numpy as np
from pptx import Presentation
from .component_registry import expand_spec
from .geometry import bbox_iou,center_distance


def _issue(page_id,element_id,kind,severity,details,auto_fixable=False,**other):
    return {'page_id':page_id,'element_id':element_id,'issue_type':kind,
            'severity':severity,'detail':details,'auto_fixable':auto_fixable,**other}


def _shape_type(shape):
    if shape.has_chart:return 'chart'
    if shape.has_table:return 'table'
    if shape.shape_type==13:return 'picture'
    if shape.shape_type==9:return 'connector'
    if shape.has_text_frame and shape.text.strip():return 'text'
    return 'shape'


def _emubox(shape,w,h):
    return [round(shape.left/w,6),round(shape.top/h,6),round(shape.width/w,6),round(shape.height/h,6)]


def _find_arrow(shape):
    if not hasattr(shape,'_element') or not hasattr(shape._element,'spPr'):return 'none'
    ln=shape._element.spPr.ln
    if ln is None:return 'none'
    xml=ln.xml
    has_head='headEnd' in xml and 'type="none"' not in xml.split('headEnd')[1].split('>')[0]
    has_tail='tailEnd' in xml and 'type="none"' not in xml.split('tailEnd')[1].split('>')[0]
    return 'both' if has_head and has_tail else ('start' if has_head else ('end' if has_tail else 'none'))


def compare_structure(spec,pptx_path,tokens,geometry_iou=.90,center_tolerance=.01):
    """Compare PPT object names to expanded JSON plus human-verified reference bboxes.
    Never guess reference boxes from ordinary content.
    """
    native=expand_spec(spec,tokens)
    prs=Presentation(str(pptx_path))
    issues=[];items=[]
    if len(native['pages'])!=len(prs.slides):
        issues.append(_issue(None,None,'slide_count_mismatch','P0',f'{len(prs.slides)} slides, expected {len(native["pages"])}'))
    for i,page in enumerate(native['pages']):
        if i>=len(prs.slides):break
        slide=prs.slides[i];pid=page.get('page_id',f'slide_{i+1:03d}')
        byname={x.name:x for x in slide.shapes}
        expected={e['id']:e for e in page.get('elements',[])}
        for id,e in expected.items():
            sh=byname.get(id)
            if sh is None:
                issues.append(_issue(pid,id,'missing_native_element','P0','PPTX missing expected ID'))
                continue
            actual=_emubox(sh,prs.slide_width,prs.slide_height)
            fam=e['type'];kind=_shape_type(sh)
            if fam=='text' and kind!='text' or fam=='connector' and kind!='connector' or fam=='chart' and kind!='chart' or fam=='table' and kind!='table':
                issues.append(_issue(pid,id,'incorrect_native_type','P0',f'{fam} expected, {kind} found'))
            if fam=='text' and sh.has_text_frame and str(e.get('text',''))!=sh.text:
                issues.append(_issue(pid,id,'text_content_mismatch','P0',f'Expected text does not match PPTX; source remains authoritative'))
            if fam=='connector':
                actual_arrow=_find_arrow(sh); expected_arrow=e.get('arrow','end')
                if actual_arrow!=expected_arrow:
                    issues.append(_issue(pid,id,'arrow_mismatch','P0',f'Arrow {actual_arrow} != {expected_arrow}'))
            if e.get('source_ref',{}).get('bbox_norm'):
                source=e['source_ref'];ref=source['bbox_norm'];iou=bbox_iou(actual,ref)
                center=center_distance(actual,ref)
                verified=bool(source.get('verified',False))
                items.append({'page_id':pid,'element_id':id,'reference_bbox_norm':ref,
                              'rendered_object_bbox_norm':actual,'bbox_iou':round(iou,4),
                              'center_distance':round(center,4),'reference_verified':verified})
                if iou < geometry_iou or center>center_tolerance:
                    issues.append(_issue(pid,id,'reference_geometry_mismatch','P1',
                        f'IoU={iou:.3f}, center-distance={center:.4f}; reference_bbox verified={verified}',
                        auto_fixable=verified and not e.get('locked',False) and fam!='connector',
                        current_bbox_norm=e.get('bbox_norm'),target_bbox_norm=ref,
                        measured_iou=round(iou,4),reference_verified=verified))
        for name,sh in byname.items():
            if name not in expected and not name.startswith('Placeholder'):
                issues.append(_issue(pid,name,'unexpected_native_element','P1','Extra PPT object not listed in page spec'))
    return {'issues':issues,'element_geometry':items,
            'P0':sum(z['severity']=='P0' for z in issues),
            'P1':sum(z['severity']=='P1' for z in issues),
            'structure_status':'REVIEW' if issues else 'PASS',
            'scope':'PPTX name/object/text/direction plus explicitly supplied reference bboxes; not visual semantic proof'}


def compare_visual(reference_path,rendered_path,output_dir,page_id='slide_001',pixel_threshold=52):
    """Align canvas by resizing only if aspect matches; outputs overlay and diff map.
    Expected font rasterization mismatch; score is for review, not automation.
    """
    reference_path=Path(reference_path);rendered_path=Path(rendered_path)
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    ref=Image.open(reference_path).convert('RGB')
    rnd=Image.open(rendered_path).convert('RGB')
    aspect1=ref.width/ref.height;aspect2=rnd.width/rnd.height
    if abs(aspect1/aspect2-1)>.018:
        return {'status':'MANUAL_REQUIRED','page_id':page_id,
                'detail':'Reference/render aspect ratios differ; crop UI/chrome or supply same slide aspect. No forced stretch.'}
    if ref.size != rnd.size:
        rnd=rnd.resize(ref.size,Image.Resampling.LANCZOS)
    mix=Image.blend(ref,rnd,.5)
    overlay=output_dir/(page_id+'_overlay.png');mix.save(overlay)
    arr_ref=np.asarray(ref,dtype=np.int16);arr_rnd=np.asarray(rnd,dtype=np.int16)
    mean=np.mean(np.abs(arr_ref-arr_rnd),axis=2)
    diff=np.max(np.abs(arr_ref-arr_rnd),axis=2)
    mask=diff>pixel_threshold
    highlight=np.asarray(rnd,dtype=np.uint8).copy()
    highlight[mask]=np.array([235,55,55],dtype=np.uint8)
    marked=output_dir/(page_id+'_difference.png');Image.fromarray(highlight).save(marked)
    return {'status':'REVIEW','page_id':page_id,'reference':str(reference_path),
            'rendered':str(rendered_path),'overlay':str(overlay),'difference_map':str(marked),
            'mean_abs_pixel_difference':round(float(mean.mean()),3),
            'fraction_pixels_above_threshold':round(float(np.mean(mask)),5),
            'threshold':pixel_threshold,
            'interpretation':'Diagnostic only; fonts, antialiasing, unsupported visuals require manual evaluation.'}


def compare_deck(spec,pptx_path,tokens,rendered_dir=None,reference_dir=None,report_dir=None,thresholds=None):
    thresholds=thresholds or {};results=compare_structure(spec,pptx_path,tokens,
        geometry_iou=float(thresholds.get('bbox_iou',.90)),
        center_tolerance=float(thresholds.get('center_distance',.01)))
    vis=[];pages=spec.get('pages',[])
    for i,page in enumerate(pages):
        pid=page.get('page_id',f'slide_{i+1:03d}')
        ref=page.get('reference_image')
        if not ref and reference_dir:
            candidate=Path(reference_dir)/f'{pid}.png'
            if candidate.exists():ref=str(candidate)
        if not ref:continue
        if not Path(ref).is_absolute():ref=str((Path(spec.get('_spec_root','.'))/ref).resolve())
        rnd=Path(rendered_dir or Path(pptx_path).parent/'preview')/f'slide_{i+1:03d}.png'
        if not rnd.exists() or not Path(ref).exists():
            vis.append({'page_id':pid,'status':'MANUAL_REQUIRED','detail':'Missing reference or render PNG'});continue
        vis.append(compare_visual(ref,rnd,Path(report_dir or Path(pptx_path).parent/'comparison'),pid,
                                  pixel_threshold=int(thresholds.get('pixel_threshold',52))))
    results['visual']=vis
    results['P0']=sum(x['severity']=='P0' for x in results['issues'])
    results['P1']=sum(x['severity']=='P1' for x in results['issues'])
    results['visual_review_required']=True
    return results
