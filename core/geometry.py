"""Pure normalized geometry helpers. No UI or PowerPoint dependency."""
from math import hypot


def clamp_box(box, max_shift=1.0):
    x,y,w,h=[float(v) for v in box]
    if not (0 < w <= 1 and 0 < h <= 1):
        raise ValueError('Box cannot fit into normalized slide without resize')
    fixed=[min(max(x,0.0),1-w), min(max(y,0.0),1-h),w,h]
    shift=hypot(fixed[0]-x,fixed[1]-y)
    if shift > max_shift + 1e-9:
        raise ValueError('Out of bounds adjustment exceeds policy limit')
    return [round(v,6) for v in fixed],shift


def bbox_iou(a,b):
    ax,ay,aw,ah=a; bx,by,bw,bh=b
    iw=max(0.0,min(ax+aw,bx+bw)-max(ax,bx))
    ih=max(0.0,min(ay+ah,by+bh)-max(ay,by))
    inter=iw*ih;union=max(0,aw*ah)+max(0,bw*bh)-inter
    return inter/union if union>0 else 0.0


def bbox_center(box):
    x,y,w,h=box
    return x+w/2,y+h/2


def center_distance(a,b):
    x1,y1=bbox_center(a);x2,y2=bbox_center(b)
    return hypot(x1-x2,y1-y2)


def anchor(box, side):
    x,y,w,h=box
    mapping={'left':(x,y+h/2),'right':(x+w,y+h/2),
             'top':(x+w/2,y),'bottom':(x+w/2,y+h),
             'center':(x+w/2,y+h/2)}
    if side not in mapping:raise ValueError('Invalid connection anchor: '+str(side))
    return mapping[side]


def resolve_connectors(elements):
    """Resolve endpoint relationships deterministically into points_norm, even if node moves."""
    lookup={e['id']:e for e in elements if 'id' in e and 'bbox_norm' in e}
    out=[]
    for e in elements:
        if e.get('type') != 'connector' or not ('from_id' in e and 'to_id' in e):
            out.append(e);continue
        start,end=e['from_id'],e['to_id']
        if start not in lookup or end not in lookup:
            raise ValueError(f'Connector {e.get("id")} refers to missing node: {start}->{end}')
        a,b=lookup[start]['bbox_norm'],lookup[end]['bbox_norm']
        xa,ya=bbox_center(a);xb,yb=bbox_center(b)
        horizontal=abs(xb-xa)>=abs(yb-ya)
        from_anchor=e.get('from_anchor', ('right' if xb>=xa else 'left') if horizontal else ('bottom' if yb>=ya else 'top'))
        to_anchor=e.get('to_anchor', ('left' if xb>=xa else 'right') if horizontal else ('top' if yb>=ya else 'bottom'))
        x1,y1=anchor(a,from_anchor);x2,y2=anchor(b,to_anchor)
        new=dict(e,points_norm=[round(v,6) for v in (x1,y1,x2,y2)])
        out.append(new)
    return out
