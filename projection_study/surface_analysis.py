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
    return dict(pixel_tangent_a_m=a,pixel_tangent_b_m=b,pixel_width_m=norm(a),pixel_height_m=norm(b),pixel_major_m=major,
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

# Uniform flux per raster pixel. The same ray/plane Jacobian used for density
# gives surface area per pixel, so inverse-square and incidence are already in
# area_density_px_m2. Applying another cosine or inverse-square would double it.
PHOTOMETRIC_ASSUMPTIONS = [
    'Estimated incident illuminance, not calibrated photometry or luminance.',
    'Uniform luminous flux per raster pixel; two-sided opaque receiver geometry.',
    'Flux = nominal lumens × stack quantity × brightness / 100; visible sources add.',
    'No measured brightness distribution, lens transmission, ageing, calibration losses, colour-mode losses or edge falloff.',
    'No screen gain, reflectance, ambient illumination, black level or colourimetry.',
]


def illuminance_lux(metrics, lumens, rx, ry, stack=1, brightness=100):
    if not all(math.isfinite(v) for v in (lumens, rx, ry, stack, brightness)) or min(rx, ry, stack)<=0 or lumens<0 or not 0<=brightness<=100:
        raise ValueError('Invalid luminous flux or raster')
    return lumens * stack * brightness / 100 / (rx * ry) * metrics['area_density_px_m2']


def weighted_statistics(pairs):
    """Pairs are (value, surface area); missing/unobservable values are omitted."""
    pairs=[(v,w) for v,w in pairs if v is not None and w>0]
    area=sum(w for v,w in pairs)
    if not area:return dict(min=None,average=None,max=None)
    return dict(min=min(v for v,w in pairs),average=sum(v*w for v,w in pairs)/area,max=max(v for v,w in pairs))


def intelligence_statistics(samples):
    # Lux includes unlit samples as zero; distance includes only visible sources.
    lux=weighted_statistics((sum(v['illuminance_lux'] for v in s['visible']),s['area_m2']) for s in samples)
    distance=weighted_statistics((min((v['distance_m'] for v in s['visible']),default=None),s['area_m2']) for s in samples)
    return dict(illuminance_min_lux=lux['min'],illuminance_average_lux=lux['average'],illuminance_max_lux=lux['max'],
        illuminance_uniformity_min_average=lux['min']/lux['average'] if lux['average'] else None,
        illuminance_uniformity_min_max=lux['min']/lux['max'] if lux['max'] else None,
        distance_min_m=distance['min'],distance_average_m=distance['average'],distance_max_m=distance['max'],
        distance_variation_m=distance['max']-distance['min'] if distance['min'] is not None else None)


def angular_pixel_radians(tangent_a, tangent_b, eye_delta):
    """Largest apparent pixel pitch: tangent Jacobian projected onto viewer plane.

    Differential pixel footprint, finite-angle 2 atan(pitch / (2 distance)).
    This includes observer foreshortening; no claim about contrast or eyesight.
    """
    distance=norm(eye_delta)
    if distance<=1e-9:return None
    direction=tuple(x/distance for x in eye_delta)
    vectors=[tuple(v[i]-direction[i]*dot(v,direction) for i in range(3)) for v in (tangent_a,tangent_b)]
    a,b=vectors;aa,bb,ab=dot(a,a),dot(b,b),dot(a,b)
    pitch=math.sqrt(max(0,(aa+bb+math.sqrt(max(0,(aa-bb)**2+4*ab*ab)))/2))
    return 2*math.atan2(pitch,2*distance)


def acuity_statistics(samples,threshold_arcmin):
    pairs=[(s.get('angular_pixel_arcmin'),s['area_m2']) for s in samples]
    stats=weighted_statistics(pairs);area=sum(w for v,w in pairs if v is not None)
    below=sum(w for v,w in pairs if v is not None and v<threshold_arcmin)
    above=sum(w for v,w in pairs if v is not None and v>=threshold_arcmin)
    return dict(acuity_min_arcmin=stats['min'],acuity_average_arcmin=stats['average'],acuity_max_arcmin=stats['max'],
        acuity_below_threshold_percent=100*below/area if area else None,
        acuity_at_or_above_threshold_percent=100*above/area if area else None,
        acuity_evaluated_area_m2=area)
