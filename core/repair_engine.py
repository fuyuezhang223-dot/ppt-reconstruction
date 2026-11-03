"""Safe, audited JSON-only repair with a bounded regression gate.
Only repositioning is authorized. Text/data/assets/style/locked elements never change.
"""
from copy import deepcopy
from pathlib import Path
import json, os
from .geometry import clamp_box,center_distance
from .ppt_builder import Builder
from .quality import inspect_pptx
from .reference_compare import compare_structure


def detect_spec_bounds(spec):
    issues=[]
    for page in spec.get('pages',[]):
        pid=page['page_id']
        for e in page.get('elements',[]):
            if 'bbox_norm' not in e:continue
            x,y,w,h=e['bbox_norm']
            if x < -1e-8 or y < -1e-8 or x+w > 1+1e-8 or y+h > 1+1e-8:
                issues.append({'page_id':pid,'element_id':e.get('id'),
                               'issue_type':'object_out_of_bounds','severity':'P0',
                               'auto_fixable':not e.get('locked',False),
                               'current_bbox_norm':e['bbox_norm'],
                               'detail':'Source JSON object lies outside normalized slide'})
    return issues


def propose_patches(spec, issues,policy):
    proposed=deepcopy(spec);patches=[];unhandled=[]
    pageids={p['page_id']:p for p in proposed['pages']}
    for issue in issues:
        pid,eid=issue.get('page_id'),issue.get('element_id')
        page=pageids.get(pid)
        if not page:
            unhandled.append({'issue':issue,'reason':'unknown page ID'});continue
        matches=[x for x in page['elements'] if x.get('id')==eid]
        if len(matches)!=1:
            unhandled.append({'issue':issue,'reason':'not a directly editable source element (e.g. expanded component child)'});continue
        e=matches[0]
        if e.get('locked'):
            unhandled.append({'issue':issue,'reason':'locked element'});continue
        kind=issue.get('issue_type')
        if kind not in policy.get('allowed_issue_types',[]):
            unhandled.append({'issue':issue,'reason':'not in fix allowlist'});continue
        before=e.get('bbox_norm')
        if not before:
            unhandled.append({'issue':issue,'reason':'no native bbox to move'});continue
        try:
            if kind=='object_out_of_bounds':
                after,delta=clamp_box(before,policy.get('max_bounds_translation_norm',.03))
            elif kind=='reference_geometry_mismatch':
                target=issue.get('target_bbox_norm')
                source=e.get('source_ref') or {}
                if not issue.get('reference_verified',False) or not source.get('verified',False) or source.get('bbox_norm')!=target:
                    unhandled.append({'issue':issue,'reason':'reference target not confirmed in source JSON'});continue
                if target[2:]!=before[2:]:
                    unhandled.append({'issue':issue,'reason':'width/height change prohibited; translation only'});continue
                after=[float(v) for v in target]
                delta=center_distance(before,after)
                if delta>policy.get('max_reference_translation_norm',.08):
                    unhandled.append({'issue':issue,'reason':'difference too large for automatic correction'});continue
            else:continue
            if any(a < 0 for a in after[:2]) or after[0]+after[2]>1 or after[1]+after[3]>1:
                raise ValueError('target still out of bounds')
        except (ValueError,TypeError) as exc:
            unhandled.append({'issue':issue,'reason':str(exc)});continue
        if any(abs(after[i]-before[i])>1e-7 for i in range(4)):
            e['bbox_norm']=after
            patches.append({'page_id':pid,'element_id':eid,'issue_type':kind,
                            'before_bbox_norm':before,'after_bbox_norm':after,
                            'distance':round(float(delta),6)})
    return proposed,patches,unhandled


def _build_and_assess(spec,tokens,dirpath,tag,project_root=None):
    target=Path(dirpath)/(tag+'.pptx')
    builder=Builder(tokens,project_root or dirpath)
    builder.build(spec,target)
    qa=inspect_pptx(target,expected_pages=len(spec['pages']),minimum_body_pt=float(tokens.get('minimum_body_pt',12)))
    structure=compare_structure(spec,target,tokens)
    bounds=detect_spec_bounds(spec)
    # P0/P1 includes the measured and the reference-labelled discrepancy.
    return target,{'machine':qa,'structure':structure,'source_bounds':bounds,
                   'P0':qa['P0']+structure['P0']+sum(i['severity']=='P0' for i in bounds),
                   'P1':qa['P1']+structure['P1']}


def _issue_signatures(evaluation):
    """Track issue identity; a lower count alone cannot conceal newly introduced errors."""
    signatures=set()
    for issue in evaluation['machine']['issues']:
        signatures.add(('machine',issue.get('level'),issue.get('page'),issue.get('detail')))
    for issue in evaluation['structure']['issues']:
        signatures.add(('structure',issue.get('severity'),issue.get('page_id'),issue.get('element_id'),issue.get('issue_type')))
    for issue in evaluation['source_bounds']:
        signatures.add(('source',issue.get('severity'),issue.get('page_id'),issue.get('element_id'),issue.get('issue_type')))
    return signatures


def repair_with_regression(spec,issues,tokens,policy,output_spec,audit_dir,project_root=None):
    audit=Path(audit_dir);audit.mkdir(parents=True,exist_ok=True)
    output_spec=Path(output_spec)
    (audit/'before.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
    candidate,patches,unhandled=propose_patches(spec,issues,policy)
    (audit/'proposed_patches.json').write_text(json.dumps(patches,ensure_ascii=False,indent=2),encoding='utf-8')
    accepted=False;regression={}
    if patches:
        try:
            before_file,before=_build_and_assess(spec,tokens,audit,'before',project_root)
            after_file,after=_build_and_assess(candidate,tokens,audit,'candidate',project_root)
            # Improvement must target at least one P0/P1; no increase in either grade.
            new_issues=_issue_signatures(after)-_issue_signatures(before)
            accepted=(after['P0']<=before['P0'] and after['P1']<=before['P1'] and
                      (after['P0']<before['P0'] or after['P1']<before['P1']) and not new_issues)
            regression={'before':before,'after':after,'accepted':accepted,
                        'new_issues':[str(x) for x in sorted(new_issues)],
                        'reason':'quality counts improved with no new issue signatures' if accepted else 'no demonstrated QA improvement or new issues detected'}
        except Exception as exc:
            regression={'accepted':False,'reason':'rebuild failed: '+str(exc)}
    else:regression={'accepted':False,'reason':'no safe patches proposed'}
    final=deepcopy(candidate if accepted else spec)
    # A copied JSON may be saved in a different directory. Preserve the original
    # source paths without rewriting the actual image/src data values.
    if project_root is not None:
        final['asset_root']=os.path.relpath(Path(project_root).resolve(),output_spec.parent.resolve())
    output_spec.parent.mkdir(parents=True,exist_ok=True)
    output_spec.write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
    (audit/'after.json').write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
    (audit/'regression.json').write_text(json.dumps(regression,ensure_ascii=False,indent=2),encoding='utf-8')
    report={'status':'ACCEPTED' if accepted else 'ROLLED_BACK',
            'proposed_count':len(patches),'accepted_count':len(patches) if accepted else 0,
            'unhandled_count':len(unhandled),'unhandled':unhandled,
            'output_spec':str(output_spec),'audit_dir':str(audit),
            'regression':{'accepted':regression['accepted'],'reason':regression['reason'],
                          'before_counts':{x:regression.get('before',{}).get(x) for x in ('P0','P1')},
                          'after_counts':{x:regression.get('after',{}).get(x) for x in ('P0','P1')}}}
    (audit/'REPAIR_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
