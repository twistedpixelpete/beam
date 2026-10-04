"""Screen geometry in metres. Pure functions; no Blender state or side effects."""
from math import sin, cos, asin, radians, degrees, pi, hypot, ceil, isfinite


def positive(**values):
    for name, value in values.items():
        if not isfinite(value) or value <= 0:
            raise ValueError(f'{name.replace("_", " ")} must be greater than zero')


def arc_values(mode, radius, angle, length, chord):
    """Chord/radius selects the minor arc; other pairs allow up to one revolution."""
    if mode == 'LENGTH_RADIUS':
        positive(radius=radius, arc_length=length); theta = length / radius
    elif mode == 'LENGTH_ANGLE':
        positive(arc_length=length, angle=angle); theta = radians(angle); radius = length / theta
    elif mode == 'CHORD_RADIUS':
        positive(chord=chord, radius=radius)
        if chord > 2 * radius: raise ValueError('Chord cannot exceed the diameter')
        theta = 2 * asin(chord / (2 * radius))
    elif mode == 'CHORD_ANGLE':
        positive(chord=chord, angle=angle); theta = radians(angle)
        if angle >= 360: raise ValueError('A 360° chord cannot define a radius')
        radius = chord / (2 * sin(theta / 2))
    else:
        positive(radius=radius, angle=angle); theta = radians(angle)
    if not 0 < theta <= 2*pi + 1e-7: raise ValueError('Arc angle must be between 0 and 360 degrees')
    theta=min(theta,2*pi)
    return dict(radius=radius, angle=degrees(theta), length=radius*theta, chord=2*radius*sin(theta/2))


def led_values(width, height, px, py, columns, rows, joint=0):
    positive(cabinet_width=width, cabinet_height=height, pixel_width=px, pixel_height=py, columns=columns, rows=rows)
    if columns*rows > 20000: raise ValueError('Use at most 20,000 cabinets per screen')
    theta=radians(joint)
    if abs(joint) >= 90: raise ValueError('Cabinet joint angle must be less than 90 degrees')
    if abs((columns-1)*joint) >= 360: raise ValueError('Faceted walls must turn less than 360°; use Closed for a seamless cylinder')
    radius=width/(2*sin(abs(theta)/2)) if abs(theta)>1e-10 else None
    chord=abs(width*sin(columns*theta/2)/sin(theta/2)) if abs(theta)>1e-10 else width*columns
    return dict(width=width*columns,height=height*rows,rx=px*columns,ry=py*rows,
                pitch_x=width/px*1000,pitch_y=height/py*1000,count=columns*rows,
                angle=(columns-1)*joint,radius=radius,chord=chord,
                equivalent_arc=radius*columns*abs(theta) if radius else width*columns)


def faceted_path(width, columns, joint):
    """N flat faces, N-1 joins. Heading change (N-1)*joint, not N*joint."""
    theta=radians(joint); points=[(0.,0.,0.)]
    for i in range(columns):
        a=(i-(columns-1)/2)*theta
        x,y,z=points[-1]; points.append((x+width*cos(a),y+width*sin(a),z))
    centre=((points[0][0]+points[-1][0])/2,(points[0][1]+points[-1][1])/2)
    return [(x-centre[0],y-centre[1],z) for x,y,z in points]


def circular_path(radius, angle, segments, convex=False, seam=0, closed=False):
    sign=1 if convex else -1; theta=radians(angle); rotate=radians(seam)
    points=[]
    for i in range(segments+1):
        a=-theta/2+theta*i/segments
        x=radius*sin(a); y=sign*radius*(1-cos(a))
        if closed: y-=sign*radius
        points.append((x*cos(rotate)-y*sin(rotate),x*sin(rotate)+y*cos(rotate),0.))
    return points


def strip(path, height, rows=1, closed=False, centre=False, distances=None):
    """Weld a closed seam in geometry, split it only in loop UVs. Front is -Y."""
    positive(height=height, rows=rows)
    if len(path)<2: raise ValueError('Screen path needs at least two points')
    lengths=[0.]
    for a,b in zip(path,path[1:]): lengths.append(lengths[-1]+sum((x-y)**2 for x,y in zip(a,b))**.5)
    if lengths[-1]<=1e-9: raise ValueError('Screen path has zero length')
    us=distances or [v/lengths[-1] for v in lengths]
    n=len(path)-1; columns=n if closed else n+1
    verts=[(x,y,z+height*j/rows-(height/2 if centre else 0)) for j in range(rows+1) for x,y,z in path[:columns]]
    faces=[]; uvs=[]
    for j in range(rows):
        for i in range(n):
            k=(i+1)%columns
            faces.append((j*columns+i,j*columns+k,(j+1)*columns+k,(j+1)*columns+i))
            uvs.append(((us[i],j/rows),(us[i+1],j/rows),(us[i+1],(j+1)/rows),(us[i],(j+1)/rows)))
    return verts,faces,uvs


def build(settings):
    """Return display geometry and explicitly labelled SI measurements."""
    p=settings; height=p.height; width=p.width; led=None
    if p.category=='LED':
        led=led_values(p.cabinet_width,p.cabinet_height,p.cabinet_px,p.cabinet_py,p.columns,p.rows,p.joint_angle if p.led_geometry=='FACETED' else 0)
        width,height=led['width'],led['height']
    positive(width=width,height=height)
    if p.screen_type not in {'FLAT','ARC','CLOSED'}: raise ValueError('This type requires a source object')
    rows=p.rows if led else p.vertical_segments
    metric=dict(width=width,height=height,length=width,chord=width,radius=0.,angle=0.,rx=led['rx'] if led else p.resolution_x,ry=led['ry'] if led else p.resolution_y)
    if p.screen_type=='FLAT':
        n=p.columns if led else p.segments
        path=[(-width/2+width*i/n,0,0) for i in range(n+1)]
    elif led and p.led_geometry=='FACETED' and p.screen_type=='ARC':
        path=faceted_path(p.cabinet_width,p.columns,p.joint_angle * (1 if p.curvature=='CONVEX' else -1))
        metric.update(length=width,chord=led['chord'],radius=led['radius'] or 0,angle=led['angle'],equivalent_arc=led['equivalent_arc'],faceted=True)
    else:
        mode='LENGTH_RADIUS' if led else 'RADIUS_ANGLE' if p.screen_type=='CLOSED' else p.arc_input
        arc=arc_values(mode,p.radius,p.angle,width if led else p.arc_length,p.chord)
        metric.update(arc);metric['width']=arc['length']
        n=max(3,p.segments) if p.quality=='SEGMENTS' else max(3,ceil(arc['length']/p.segment_length))
        if n>4096: raise ValueError('Requested segment length needs more than 4096 segments')
        path=circular_path(arc['radius'],arc['angle'],n,p.curvature=='CONVEX',p.seam_angle,p.screen_type=='CLOSED')
    closed=p.screen_type=='CLOSED' and abs(metric['angle']-360)<1e-5
    if p.screen_type=='ARC' and abs(metric['angle']-360)<1e-5: closed=True
    if (len(path)-1)*rows>200000: raise ValueError('Screen exceeds 200,000 quads; reduce subdivisions')
    # Circular equal angles are equal true arc distances, not chord projection.
    geom=strip(path,height,rows,closed,p.origin=='CENTRE')
    if led:metric.update(pitch_x=led['pitch_x'],pitch_y=led['pitch_y'],count=led['count'])
    return geom,metric
