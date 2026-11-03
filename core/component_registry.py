"""Expand semantic composite components into the existing native element schema.
Do not silently redesign reference geometry: explicit bbox_norm always takes precedence.
"""
from copy import deepcopy
from .geometry import resolve_connectors

COMPONENTS=('title_block','icon_card','flow_node','horizontal_flow','table_block','image_text','timeline','comparison_matrix')

def _bbox(item, default):
    return list(item.get('bbox_norm', default))

def _tx(id,bbox,text,size=14,**opts):
    return {'type':'text','id':id,'bbox_norm':bbox,'text':str(text),'font_size':size,**opts}

def _sh(id,bbox,fill='#EAF3F9',**opts):
    return {'type':'shape','id':id,'bbox_norm':bbox,'shape':'roundrect','fill':fill,**opts}

def _copy_props(raw, elems):
    # A composite lock is inherited. Source reference is not copied across child
    # elements because a composite reference bbox is not a child's bbox.
    for e in elems:
        e['component_parent']=raw['id']
        if raw.get('locked'):e['locked']=True
        if raw.get('confidence') is not None:e['confidence']=raw['confidence']
    return elems

def title_block(c,t):
    x,y,w,h=c['bbox_norm']; id=c['id']; title_h=min(h*.63,.115)
    elems=[_tx(id+'/title',[x,y,w,title_h],c.get('title',''),c.get('title_size',t.get('title_size_pt',26)),bold=True,color=c.get('title_color',t.get('primary_color','#1E5082')))]
    if c.get('subtitle'):
        elems.append(_tx(id+'/subtitle',[x,y+title_h,w,max(.02,h-title_h)],c['subtitle'],c.get('subtitle_size',14),color=c.get('subtitle_color','#55738F')))
    if c.get('underline'):
        elems.insert(0,{'type':'shape','id':id+'/rule','shape':'rect','bbox_norm':[x,y+h-.008,w*.28,.005],'fill':c.get('title_color','#1E5082')})
    return elems

def flow_node(c,t):
    x,y,w,h=c['bbox_norm'];id=c['id'];bg=c.get('fill','#EAF3F9')
    elems=[_sh(id+'/box',[x,y,w,h],bg,line_color=c.get('line_color','#B5D1E6'))]
    if c.get('icon_id'):
        elems.append({'type':'icon','id':id+'/icon','icon_id':c['icon_id'],'bbox_norm':[x+w*.43,y+h*.08,w*.14,h*.28],'color':c.get('color','#1E5082')})
    title_y=y+h*(.38 if c.get('icon_id') else .18)
    elems.append(_tx(id+'/title',[x+w*.06,title_y,w*.88,h*.30],c.get('title',''),c.get('font_size',15),align='center',bold=True))
    if c.get('description'):
        elems.append(_tx(id+'/description',[x+w*.06,y+h*.71,w*.88,h*.22],c['description'],c.get('description_size',12),align='center'))
    return elems

def icon_card(c,t):
    x,y,w,h=c['bbox_norm'];id=c['id']
    if not c.get('icon_id'):
        raise ValueError('icon_card requires fixed icon_id (no guessed symbol)')
    elems=[_sh(id+'/box',[x,y,w,h],c.get('fill','#EAF3F9'),line_color=c.get('line_color','#B5D1E6')),
           {'type':'icon','id':id+'/icon','icon_id':c['icon_id'],'bbox_norm':[x+w*.39,y+h*.12,w*.22,h*.28],'color':c.get('color','#1E5082')},
           _tx(id+'/title',[x+w*.08,y+h*.50,w*.84,h*.16],c.get('title',''),c.get('title_size',16),bold=True,align='center')]
    if c.get('description'):
        elems.append(_tx(id+'/description',[x+w*.06,y+h*.72,w*.88,h*.18],c['description'],c.get('description_size',12),align='center'))
    return elems

def horizontal_flow(c,t):
    x,y,w,h=c['bbox_norm'];nodes=c.get('nodes',[]);prefix=c['id']
    if not 2<=len(nodes)<=8:raise ValueError('horizontal_flow expects 2..8 nodes')
    gap=float(c.get('gap_norm',.047));node_w=(w-gap*(len(nodes)-1))/len(nodes)
    if node_w<=0:raise ValueError('Not enough room for flow nodes')
    out=[];ids=[]
    for i,node in enumerate(nodes):
        nid=prefix+'/'+str(node['id']);ids.append(nid+'/box')
        b=_bbox(node,[x+(node_w+gap)*i,y,node_w,h])
        out.extend(flow_node({**node,'id':nid,'bbox_norm':b,'fill':node.get('fill',c.get('fill','#EAF3F9'))},t))
        if node.get('source_bbox_norm'):
            for sub in out:
                if sub['id']==nid+'/box':
                    sub['source_ref']={'bbox_norm':node['source_bbox_norm'],'verified':node.get('source_verified',False)}
    for i in range(len(ids)-1):
        out.append({'type':'connector','id':prefix+f'/edge_{i+1}',
                    'from_id':ids[i],'to_id':ids[i+1],
                    'arrow':c.get('arrow','end'),'line_width':c.get('line_width',2),
                    'color':c.get('arrow_color',t.get('primary_color','#1E5082'))})
    # Ensure arrows render beneath boxes (native connectors are placed first).
    return [e for e in out if e['type']=='connector']+[e for e in out if e['type']!='connector']

def table_block(c,t):
    return [{'type':'table','id':c['id']+'/table','bbox_norm':c['bbox_norm'],
             'rows':c['rows'],'font_size':c.get('font_size',12),
             'header_fill':c.get('header_fill','#DCEAF4'),
             'body_fill':c.get('body_fill','#FFFFFF')}]

def image_text(c,t):
    x,y,w,h=c['bbox_norm'];id=c['id'];side=c.get('image_side','left');pct=float(c.get('image_fraction',.43))
    if not (0.2<=pct<=0.75):raise ValueError('image_fraction out of range')
    gap=w*.04;imgw=(w-gap)*pct; txtw=w-imgw-gap
    xi=x if side=='left' else x+w-imgw
    xt=x+imgw+gap if side=='left' else x
    if 'src' not in c:raise ValueError('image_text requires src')
    return [{'type':'image','id':id+'/image','bbox_norm':[xi,y,imgw,h],'src':c['src'],'fit':'contain'},
            _tx(id+'/title',[xt,y,txtw,h*.29],c.get('title',''),c.get('title_size',18),bold=True),
            _tx(id+'/body',[xt,y+h*.33,txtw,h*.60],c.get('text',''),c.get('font_size',14),v_align='top')]

def timeline(c,t):
    x,y,w,h=c['bbox_norm'];id=c['id'];items=c.get('items',[])
    if not 2<=len(items)<=8:raise ValueError('timeline items 2..8')
    yc=y+h*.46
    out=[{'type':'shape','id':id+'/axis','shape':'rect','bbox_norm':[x,yc,w,.004],
          'fill':c.get('line_color','#8EA9C4')}]
    for i,item in enumerate(items):
        cx=x+w*(i+.5)/len(items)
        out.append({'type':'shape','id':id+f'/point_{i+1}','shape':'ellipse','bbox_norm':[cx-.007,yc-.009,.014,.018],
                    'fill':c.get('point_color','#2B7FBA')})
        out.append(_tx(id+f'/label_{i+1}',[cx-w/(2*len(items))+.005,yc+h*.10,w/len(items)-.01,h*.32],item.get('label',''),c.get('font_size',12),align='center'))
    return out

def comparison_matrix(c,t):
    x,y,w,h=c['bbox_norm'];id=c['id'];columns=c.get('columns',[])
    if len(columns)!=2:raise ValueError('comparison_matrix requires exactly 2 columns')
    gap=w*.04;cw=(w-gap)/2;out=[]
    for i,cl in enumerate(columns):
        bx=x+i*(cw+gap);bid=id+f'/col_{i+1}'
        out.append(_sh(bid+'/box',[bx,y,cw,h],cl.get('fill','#EAF3F9')))
        out.append(_tx(bid+'/title',[bx+cw*.07,y+h*.10,cw*.86,h*.24],cl.get('title',''),c.get('title_size',18),bold=True,align='center'))
        out.append(_tx(bid+'/body',[bx+cw*.07,y+h*.39,cw*.86,h*.50],cl.get('text',''),c.get('font_size',14),v_align='top'))
    return out

REGISTRY={key:globals()[key] for key in COMPONENTS}

def expand_spec(spec,tokens):
    """Return a fully native spec with deterministic names. Never mutate input."""
    result=deepcopy(spec)
    for page in result.get('pages',[]):
        native=[]
        for raw in page.get('elements',[]):
            if 'component' in raw:
                if raw['component'] not in REGISTRY:raise ValueError('Unknown component: '+str(raw['component']))
                if not raw.get('id') or not raw.get('bbox_norm'):raise ValueError('Composite needs id and bbox_norm')
                native.extend(_copy_props(raw,REGISTRY[raw['component']](raw,tokens)))
            else:native.append(raw)
        ids=[e.get('id') for e in native]
        if any(not x for x in ids) or len(ids)!=len(set(ids)):
            raise ValueError('All native elements must have globally unique nonempty IDs within page')
        page['elements']=resolve_connectors(native)
    return result
