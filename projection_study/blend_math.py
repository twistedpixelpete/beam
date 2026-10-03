"""Nominal planar overlap; independent of Blender and photometric rendering."""
def overlap_values(value,mode,pixels,length):
    fraction=value/pixels if mode=='PIXELS' else value/100 if mode=='PERCENT' else value/length
    fraction=max(0,min(.95,fraction))
    return dict(pixels=fraction*pixels,percent=fraction*100,metres=fraction*length,fraction=fraction)


def cells(layout,count,columns):
    columns=count if layout=='HORIZONTAL' else 1 if layout=='VERTICAL' else max(1,columns)
    return [(i%columns,i//columns) for i in range(count)]


def adjacent(layout,count,columns):
    positions=cells(layout,count,columns); lookup={p:i for i,p in enumerate(positions)}
    return [(i,lookup[q],axis) for i,(x,y) in enumerate(positions)
            for q,axis in [((x+1,y),'H'),((x,y+1),'V')] if q in lookup]


def intersection(subject,clip):
    """Convex polygon intersection in a shared nominal-plane coordinate system."""
    def ccw(poly):
        area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))
        return list(poly if area>=0 else reversed(poly))
    output=ccw(subject); clip=ccw(clip)
    for a,b in zip(clip,clip[1:]+clip[:1]):
        source=output; output=[]
        if not source: break
        def distance(p): return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        previous=source[-1]; dp=distance(previous)
        for current in source:
            dc=distance(current)
            if (dc>=0)!=(dp>=0):
                t=dp/(dp-dc)
                output.append((previous[0]+t*(current[0]-previous[0]),previous[1]+t*(current[1]-previous[1])))
            if dc>=0: output.append(current)
            previous=current; dp=dc
    return output
