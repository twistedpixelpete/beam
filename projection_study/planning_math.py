"""Pure inverse and rectangular layout planning, in physical metres.

Forward values always come from projection_math.calculate; these are constraint
solvers, not a second projection engine.
"""
import math
from .projection_math import calculate


def positive(*values):
    if not all(math.isfinite(v) and v>0 for v in values):
        raise ValueError('Enter finite values greater than zero')


def desired_width(field,value,rx,ry):
    positive(value,rx,ry)
    return {'WIDTH':lambda:value,'HEIGHT':lambda:value*rx/ry,
            'DENSITY':lambda:rx/value,'PIXEL_SIZE':lambda:rx*value}[field]()


def inverse(field,value,mode,distance,ratio,rx,ry,position_locked=False,lens_locked=False):
    positive(value,distance,ratio,rx,ry)
    if mode=='AUTO':mode='POSITION' if field=='DISTANCE' or lens_locked else 'LENS'
    if field=='RATIO':
        if lens_locked:raise ValueError('Throw ratio is locked')
        if mode=='POSITION':raise ValueError('Choose Lens or Auto to change throw ratio')
        result=(distance,value,'LENS')
    elif field=='DISTANCE':
        if mode=='LENS':raise ValueError('Choose Projector Position to change throw distance')
        if position_locked:raise ValueError('Projector position is locked')
        result=(value,ratio,'POSITION')
    else:
        width=desired_width(field,value,rx,ry)
        if mode=='LENS':
            if lens_locked:raise ValueError('Throw ratio is locked; choose Position or unlock it')
            result=(distance,distance/width,'LENS')
        else:
            if position_locked:raise ValueError('Projector position is locked; choose Lens or unlock it')
            result=(width*ratio,ratio,'POSITION')
    if not .05<=result[1]<=100:raise ValueError('Required throw ratio is outside 0.05–100')
    return result


def fraction(value,mode,pixels):
    if not math.isfinite(value) or value<0:raise ValueError('Overlap must be finite and non-negative')
    f=value/pixels if mode=='PIXELS' else value/100
    if not 0<=f<.95:raise ValueError('Overlap must be below 95% of one image')
    return f


def plan(width,height,rx,ry,ratio,layout='HORIZONTAL',count=3,columns=2,rows=2,
         auto=False,overlap_h=200,overlap_v=200,units='PIXELS',distance=10,
         fixed_distance=False,max_count=32,min_throw=.1,max_throw=100):
    positive(width,height,rx,ry,ratio,distance,min_throw,max_throw)
    if max_throw<min_throw:raise ValueError('Maximum throw must be at least the minimum')
    if not .05<=ratio<=100:raise ValueError('Template throw ratio is outside 0.05–100')
    if layout=='HORIZONTAL':overlap_v=0
    elif layout=='VERTICAL':overlap_h=0
    if units=='METRES':
        if not all(math.isfinite(v) and v>=0 for v in (overlap_h,overlap_v)):raise ValueError('Overlap must be non-negative')
        fh=fv=None
    else:fh=fraction(overlap_h,units,rx);fv=fraction(overlap_v,units,ry)
    aspect=ry/rx
    def candidate(c,r):
        if units=='METRES':
            need=max((width+(c-1)*overlap_h)/c,(height+(r-1)*overlap_v)/(r*aspect))
        else:need=max(width/(c-(c-1)*fh),height/(aspect*(r-(r-1)*fv)))
        d=distance if fixed_distance or auto else need*ratio
        if not min_throw<=d<=max_throw:return None
        m=calculate(d,ratio,rx,ry)
        oh=overlap_h if units=='METRES' else m.width*fh
        ov=overlap_v if units=='METRES' else m.height*fv
        if oh>=m.width*.95 or ov>=m.height*.95:return None
        cw=c*m.width-(c-1)*oh;ch=r*m.height-(r-1)*ov
        if (c-1)*(m.width-oh)>width+1e-6 or (r-1)*(m.height-ov)>height+1e-6:return None
        if cw+1e-6<width or ch+1e-6<height:return None
        return dict(columns=c,rows=r,count=c*r,distance=d,width=m.width,height=m.height,
                    coverage_width=cw,coverage_height=ch,coverage=100.,density=m.pixels_per_metre,
                    overlap_h=dict(metres=oh,pixels=oh/m.width*rx,percent=oh/m.width*100),
                    overlap_v=dict(metres=ov,pixels=ov/m.height*ry,percent=ov/m.height*100))
    if auto:
        candidates=[]
        for n in range(1,max_count+1):
            shapes=[(n,1)] if layout=='HORIZONTAL' else [(1,n)] if layout=='VERTICAL' else [(c,n//c) for c in range(1,n+1) if n%c==0]
            for c,r in shapes:
                result=candidate(c,r)
                if result:candidates.append(result)
            if candidates:return min(candidates,key=lambda v:(v['coverage_width']*v['coverage_height'],v['columns']))
        raise ValueError('Coverage incomplete: increase throw, change layout, or raise maximum count')
    c,r=(count,1) if layout=='HORIZONTAL' else (1,count) if layout=='VERTICAL' else (columns,rows)
    if min(c,r)<1 or c*r>max_count:raise ValueError(f'Use 1–{max_count} projectors')
    result=candidate(c,r)
    if not result:raise ValueError('Coverage incomplete or outside allowed throw range; adjust count, throw or overlap')
    return result
