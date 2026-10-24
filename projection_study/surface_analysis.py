"""Pure differential perspective analysis. Lengths in metres; no Blender dependency."""
import math

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def local_metrics(point, normal, ratio, rx, ry, shift_h=0, shift_v=0, reference_density=None):
    """Ray/plane Jacobian at a surface point, per raster pixel, in projector space."""
    if not all(math.isfinite(v) for v in (*point,*normal,ratio,rx,ry,shift_h,shift_v)) or min(ratio,rx,ry)<=0 or norm(normal)==0:raise ValueError('Finite positive optics and a nonzero surface normal are required')
    z=-point[2]
    if z<=1e-9:return None
    u=point[0]*ratio/z+.5-shift_h/100
    v=point[1]*ratio*rx/(z*ry)+.5-shift_v/100
    if not (0<=u<=1 and 0<=v<=1):return None
    ray=tuple(p/z for p in point);den=dot(normal,ray)
    if abs(den)<1e-10:return None
    derivatives=[]
    for axis in (0,1):
        d=tuple((1/(ratio*rx) if i==axis else 0) for i in range(3))
        derivatives.append(tuple(z*(d[i]-ray[i]*dot(normal,d)/den) for i in range(3)))
    a,b=derivatives;aa,bb,ab=dot(a,a),dot(b,b),dot(a,b)
    disc=math.sqrt(max(0,(aa-bb)**2+4*ab*ab))
    major=math.sqrt(max(0,(aa+bb+disc)/2));minor=math.sqrt(max(0,(aa+bb-disc)/2))
    if minor<=1e-12:return None
    density=1/major
    return dict(pixel_width_m=norm(a),pixel_height_m=norm(b),pixel_major_m=major,
        pixel_minor_m=minor,density_px_m=density,area_density_px_m2=1/(major*minor),
        anisotropy=major/minor,incidence_deg=math.degrees(math.acos(min(1,abs(den)/(norm(normal)*norm(ray))))),
        relative_stretch=major*reference_density if reference_density else None)

def summarise(samples):
    total=sum(s['area_m2'] for s in samples)
    def area(key):return sum(s['area_m2'] for s in samples if s[key])
    nominal=area('nominal');visible=area('visible');overlap=sum(s['area_m2'] for s in samples if len(s['visible'])>1)
    covered=[(max(s['visible'],key=lambda v:v['density_px_m']),s['area_m2']) for s in samples if s['visible']]
    values=[v['density_px_m'] for v,w in covered]
    average=sum(v['density_px_m']*w for v,w in covered)/visible if visible else None
    occluded=sum(bool(s['nominal']) and not bool(s['visible']) for s in samples)
    return dict(surface_area_m2=total,nominal_covered_area_m2=nominal,visible_covered_area_m2=visible,
        coverage_percent=100*visible/total if total else 0,uncovered_percent=100*(1-visible/total) if total else 0,
        overlap_area_m2=overlap,overlap_percent=100*overlap/total if total else 0,overlap_percent_of_covered=100*overlap/visible if visible else 0,
        density_min_px_m=min(values) if values else None,density_max_px_m=max(values) if values else None,
        density_average_px_m=average,density_variation_percent=100*(max(values)-min(values))/average if average else None,
        min_anisotropy=min((v['anisotropy'] for v,w in covered),default=None),
        average_anisotropy=sum(v['anisotropy']*w for v,w in covered)/visible if visible else None,
        max_anisotropy=max((v['anisotropy'] for v,w in covered),default=None),
        sample_count=len(samples),occluded_sample_count=occluded,occluded_sample_percent=100*occluded/len(samples) if samples else 0)
