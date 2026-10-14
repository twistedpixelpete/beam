"""Exact polygon-union area by a vertical sweep over linear edge events."""
def union_area(polygons):
    polygons=[p for p in polygons if len(p)>=3]
    edges=[(a,b) for p in polygons for a,b in zip(p,p[1:]+p[:1])]
    xs={v[0] for p in polygons for v in p}
    for i,(a,b) in enumerate(edges):
        dx=b[0]-a[0];dy=b[1]-a[1]
        for c,d in edges[i+1:]:
            ex=d[0]-c[0];ey=d[1]-c[1];den=dx*ey-dy*ex
            if abs(den)<1e-12:continue
            t=((c[0]-a[0])*ey-(c[1]-a[1])*ex)/den
            u=((c[0]-a[0])*dy-(c[1]-a[1])*dx)/den
            if 0<t<1 and 0<u<1:xs.add(a[0]+t*dx)
    xs=sorted(xs);area=0
    for left,right in zip(xs,xs[1:]):
        if right-left<1e-12:continue
        x=(left+right)/2;intervals=[]
        for p in polygons:
            ys=[]
            for a,b in zip(p,p[1:]+p[:1]):
                if min(a[0],b[0])<x<max(a[0],b[0]):ys.append(a[1]+(x-a[0])*(b[1]-a[1])/(b[0]-a[0]))
            if len(ys)>=2:intervals.append((min(ys),max(ys)))
        intervals.sort();length=0;end=None
        for low,high in intervals:
            if end is None or low>end:length+=high-low;end=high
            elif high>end:length+=high-end;end=high
        area+=(right-left)*length
    return area
