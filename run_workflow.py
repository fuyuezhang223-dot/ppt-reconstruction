"""Reusable PPTX workflow CLI: build / compare / repair / QA / icon search."""
from pathlib import Path
import argparse,json,sys
from core.icon_library import IconLibrary
from core.ppt_builder import Builder
from core.component_registry import expand_spec
from core.quality import inspect_pptx,save_report,render_preview
from core.reference_compare import compare_deck
from core.repair_engine import detect_spec_bounds,repair_with_regression
from core.image_analyzer import analyze_batch

ROOT=Path(__file__).resolve().parent

def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def main():
    ap=argparse.ArgumentParser(description='PPT Reconstruction Skill 1.0.0 (workflow engine 4.4.1)')
    ap.add_argument('--version', action='version', version='PPT Reconstruction Skill 1.0.0 | workflow 4.4.1')
    sub=ap.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build');b.add_argument('--spec',required=True);b.add_argument('--output',default='outputs/result.pptx');b.add_argument('--tokens');b.add_argument('--no-render',action='store_true');b.add_argument('--compare',action='store_true')
    si=sub.add_parser('search-icon');si.add_argument('term');si.add_argument('--limit',type=int,default=8)
    q=sub.add_parser('qa');q.add_argument('pptx');q.add_argument('--min-font',type=float,default=12)
    c=sub.add_parser('compare');c.add_argument('--spec',required=True);c.add_argument('--pptx',required=True);c.add_argument('--rendered-dir');c.add_argument('--reference-dir');c.add_argument('--output',default='outputs/VISUAL_QA.json');c.add_argument('--tokens');c.add_argument('--thresholds')
    r=sub.add_parser('repair');r.add_argument('--spec',required=True);r.add_argument('--report');r.add_argument('--output-spec',required=True);r.add_argument('--audit-dir',default='outputs/repair_audit');r.add_argument('--tokens');r.add_argument('--policy')
    ai=sub.add_parser('analyze-image',help='OCR plus OpenCV visual-structure proposals for slide images')
    ai.add_argument('--input',required=True,help='one image file or a folder of slide images')
    ai.add_argument('--output-dir',default='outputs/image_analysis')
    ai.add_argument('--engine',choices=['auto','rapidocr','tesseract','none'],default='auto')
    ai.add_argument('--lang',default='chi_sim+eng',help='Tesseract language code; default chi_sim+eng')
    ai.add_argument('--min-confidence',type=float,default=0.75)
    ai.add_argument('--no-shapes',action='store_true',help='skip optional OpenCV geometry, arrow, table, icon and layout proposals')
    ai.add_argument('--page-width',type=float,help='override output slide width in inches')
    ai.add_argument('--page-height',type=float,default=7.5)
    ai.add_argument('--build-draft',action='store_true',help='also build a first-pass editable PPTX')
    a=ap.parse_args()
    if a.command=='search-icon':
        for item in IconLibrary().search(a.term,a.limit):print(f"{item['id']}\t{item['name_zh']}\t{item['relative_path']}\t{item['priority']}")
        return 0
    if a.command=='analyze-image':
        summary=analyze_batch(Path(a.input).resolve(),Path(a.output_dir).resolve(),
                              engine=a.engine,lang=a.lang,min_confidence=a.min_confidence,
                              detect_shapes=not a.no_shapes,page_width_in=a.page_width,
                              page_height_in=a.page_height)
        print(f"Image analysis: {summary['status']} | pages={summary['image_count']}")
        print('Draft spec:',summary['draft_spec'])
        if a.build_draft:
            spec=read_json(summary['draft_spec'])
            tokens=read_json(ROOT/'config/design_tokens.json')
            out=Path(a.output_dir).resolve()/'draft.pptx'
            builder=Builder(tokens,Path(a.output_dir).resolve())
            builder.build(spec,out)
            report=inspect_pptx(out,expected_pages=len(spec['pages']),minimum_body_pt=float(tokens.get('minimum_body_pt',12)))
            report['warnings']=list(dict.fromkeys(builder.warnings))
            report['render']=render_preview(out,out.parent/'preview')
            save_report(report,out.parent/'QA_REPORT.json')
            print(f"Draft PPTX: {out} | P0={report['P0']} P1={report['P1']} | Render={report['render']['status']}")
        print('注意：OCR 与结构候选草稿必须逐页人工核对，不能视为已完成的高保真复刻。')
        return 0
    if a.command=='qa':
        report=inspect_pptx(a.pptx,minimum_body_pt=a.min_font)
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 2 if report['P0'] or report['P1'] else 0
    tokens=read_json(a.tokens or ROOT/'config/design_tokens.json')
    source=Path(a.spec).resolve();spec=read_json(source)
    try:
        from jsonschema import validate
        validate(instance=spec,schema=read_json(ROOT/'schemas/page_spec.schema.json'))
    except ImportError:
        raise RuntimeError('Please install jsonschema: pip install -r requirements.txt')
    source_root=(source.parent/spec.get('asset_root','.')).resolve()
    if a.command=='compare':
        spec['_spec_root']=str(source_root)
        result=compare_deck(spec,Path(a.pptx).resolve(),tokens,
                            rendered_dir=a.rendered_dir,reference_dir=a.reference_dir,
                            report_dir=Path(a.output).resolve().parent/'comparison',
                            thresholds=read_json(a.thresholds or ROOT/'config/qa_thresholds.json'))
        save_report(result,a.output)
        print(f"VISUAL_QA: {a.output}, P0={result['P0']}, P1={result['P1']} (visual manual review required)")
        return 2 if result['P0'] or result['P1'] else 0
    if a.command=='repair':
        issues=detect_spec_bounds(spec)
        if a.report:
            report=read_json(a.report)
            issues+=report.get('issues',[])
        outcome=repair_with_regression(spec,issues,tokens,read_json(a.policy or ROOT/'config/repair_policy.json'),a.output_spec,a.audit_dir,project_root=source_root)
        print(json.dumps({k:v for k,v in outcome.items() if k!='unhandled'},ensure_ascii=False,indent=2))
        return 0 if outcome['status']=='ACCEPTED' else 3
    # BUILD
    out=Path(a.output).resolve()
    builder=Builder(tokens,source_root)
    builder.build(spec,out)
    report=inspect_pptx(out,expected_pages=len(spec['pages']),minimum_body_pt=float(tokens.get('minimum_body_pt',12)))
    report['warnings']=list(dict.fromkeys(builder.warnings))
    report['route']=spec.get('route','strict_reconstruction')
    report['render']={'status':'SKIPPED'} if a.no_render else render_preview(out,out.parent/'preview')
    if a.compare:
        spec['_spec_root']=str(source_root)
        compare=compare_deck(spec,out,tokens,rendered_dir=out.parent/'preview',
                 report_dir=out.parent/'comparison',thresholds=read_json(ROOT/'config/qa_thresholds.json'))
        save_report(compare,out.parent/'VISUAL_QA.json')
        report['comparison']={'P0':compare['P0'],'P1':compare['P1'],'manual_visual_review':True}
    save_report(report,out.parent/'QA_REPORT.json')
    (out.parent/'reconstruction_inventory.json').write_text(json.dumps(builder.inventory,ensure_ascii=False,indent=2),encoding='utf-8')
    actual=expand_spec(spec,tokens)
    manifest=[{'page_id':p.get('page_id',f'slide_{n+1:03d}'),'source_type':p.get('source_type','manual_spec'),
               'route':spec.get('route','strict_reconstruction'), 'aspect_ratio':f'{builder.width}:{builder.height}',
               'element_count':len(p.get('elements',[])),'expanded_native_elements':len(actual['pages'][n]['elements']),
               'blocking_issue':p.get('blocking_issue')} for n,p in enumerate(spec['pages'])]
    (out.parent/'page_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PPTX: {out}\nMachine QA: P0={report["P0"]} P1={report["P1"]} Render={report["render"]["status"]}')
    if a.compare:
        print(f'Comparison QA: P0={compare["P0"]} P1={compare["P1"]}; independent visual review is still required')
        print('VISUAL_QA:',out.parent/'VISUAL_QA.json')
    print('Caution: programmatic QA does not certify semantic or pixel-perfect reconstruction.')
    return 2 if report['P0'] or report['P1'] or (a.compare and (compare['P0'] or compare['P1'])) else 0

if __name__=='__main__':sys.exit(main())
